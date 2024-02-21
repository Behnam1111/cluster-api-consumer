import httpx
from redis import Redis
from typing import List
from rq import Queue, Retry
from datetime import timedelta
from dotenv import load_dotenv
import logging

from config import Config
from exceptions.custom_exceptions import GroupAlreadyExistsException, FailedToCreateGroupInAllNodes, \
    FailedToDeleteGroupFromAllNodes

logger = logging.getLogger(__name__)

load_dotenv()
redis_conn = Redis(decode_responses=True)
# redis_conn = Redis(decode_responses=True, host="redis")
task_queue = Queue(connection=redis_conn)


class ClusterAPIConsumer:
    def __init__(self):
        self.hosts = Config().get_hosts()
        self.endpoint_group = "/v1/group"

    async def create_group(self, group_id: str) -> bool:
        successfully_created_hosts: List[str] = []
        for host in self.hosts:
            response = await self._make_request(method="post", host=host, group_id=group_id)
            if response and response.status_code == httpx.codes.CREATED:
                successfully_created_hosts.append(host)

            else:
                get_response = await self._make_request(method="get", host=host, group_id=group_id)
                if get_response and get_response.status_code == httpx.codes.OK:
                    raise GroupAlreadyExistsException()
                else:
                    await self._rollback_created_groups(
                        group_id, successfully_created_hosts
                    )
                    raise FailedToCreateGroupInAllNodes()
        return True

    async def delete_group(self, group_id: str) -> bool:
        successfully_deleted_hosts: List[str] = []
        for host in self.hosts:
            response = await self._make_request(method="delete", host=host, group_id=group_id)
            if response and response.status_code == httpx.codes.OK:
                successfully_deleted_hosts.append(host)

            else:
                await self._rollback_deleted_groups(group_id, successfully_deleted_hosts)
                raise FailedToDeleteGroupFromAllNodes()
        return True

    async def _make_request(
        self, method: str, host: str, group_id: str
    ) -> httpx.Response | None:
        async with httpx.AsyncClient(trust_env=False) as async_client:
            url = f"http://{host.strip()}{self.endpoint_group}"
            logger.info(f"url is this {url}")
            try:
                if method == "post":
                    return await async_client.post(url, json={"groupId": group_id})
                elif method == "delete":
                    return await async_client.delete(url, params={"groupId": group_id})
                elif method == "get":
                    return await async_client.get(url, params={"groupId": group_id})
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
            return None

    async def _rollback_created_groups(
            self, group_id: str, hosts_to_rollback: List[str]
    ):
        for host in hosts_to_rollback:
            response = await self._make_request("delete", host, group_id)
            if not(response and response.status_code == httpx.codes.OK):
                task_queue.enqueue_in(
                    time_delta=timedelta(seconds=60),
                    func=self._rollback_created_groups,
                    args=(group_id, [host]),
                )

    async def _rollback_deleted_groups(
            self, group_id: str, hosts_to_rollback: List[str]
    ):
        for host in hosts_to_rollback:
            response = await self._make_request("post", host, group_id)
            if not (response and response.status_code == httpx.codes.CREATED):
                task_queue.enqueue(
                    self._rollback_deleted_groups,
                    retry=Retry(max=3, interval=10),
                    args=("post", host, group_id),
                )
