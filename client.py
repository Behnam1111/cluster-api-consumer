import httpx
import logging
from redis import Redis
from typing import List
from rq import Queue, Retry
from datetime import timedelta
from dotenv import load_dotenv

from config import Config

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
redis_conn = Redis(decode_responses=True)
q = Queue(connection=redis_conn)


class ClusterAPIConsumer:
    def __init__(self):
        self.hosts = Config().get_hosts()
        self.endpoint_group = "/v1/group"

    async def create_group(self, group_id: str) -> bool:
        successful_created_hosts: List[str] = []
        for host in self.hosts:
            response = await self.make_request("post", host, group_id)
            if not self._create_group_id_was_successful(response):
                await self.rollback_created_groups(group_id, successful_created_hosts)
                return False
            successful_created_hosts.append(host)
        return True

    async def delete_group(self, group_id: str) -> bool:
        successful_deleted_hosts: List[str] = []
        for host in self.hosts:
            response = await self.make_request("delete", host, group_id)
            if not self._delete_group_id_was_successful(response):
                await self.rollback_deleted_groups(group_id, successful_deleted_hosts)
                return False
            successful_deleted_hosts.append(host)
        return True

    async def make_request(
        self, method: str, host: str, group_id: str
    ) -> httpx.Response | None:
        async with httpx.AsyncClient(trust_env=False) as async_client:
            url = f"http://{host.strip()}{self.endpoint_group}"
            try:
                if method == "post":
                    return await async_client.post(url, json={"groupId": group_id})
                elif method == "delete":
                    return await async_client.delete(url, params={"groupId": group_id})
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
            return None

    def _create_group_id_was_successful(self, response: httpx.Response | None) -> bool:
        if response and response.status_code == httpx.codes.CREATED:
            return True
        return False

    def _delete_group_id_was_successful(self, response: httpx.Response | None) -> bool:
        if response and response.status_code == httpx.codes.OK:
            return True
        return False

    async def rollback_created_groups(
        self, group_id: str, hosts_to_rollback: List[str]
    ):
        for host in hosts_to_rollback:
            result = await self.make_request("delete", host, group_id)
            if not self._delete_group_id_was_successful(result):
                q.enqueue_in(
                    time_delta=timedelta(seconds=60),
                    func=self.rollback_created_groups,
                    args=(group_id, [host]),
                )

    async def rollback_deleted_groups(
        self, group_id: str, hosts_to_rollback: List[str]
    ):
        for host in hosts_to_rollback:
            result = await self.make_request("post", host, group_id)
            if not self._create_group_id_was_successful(result):
                q.enqueue(
                    self.make_request,
                    retry=Retry(max=3, interval=10),
                    args=("post", host, group_id),
                )
