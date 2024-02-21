import logging
from enum import Enum
from typing import List
from datetime import timedelta

import httpx
from rq import Queue
from redis import Redis
from dotenv import load_dotenv

from config import Config
from exceptions.custom_exceptions import (
	GroupAlreadyExistsException,
	FailedToCreateGroupInAllNodes,
	FailedToDeleteGroupFromAllNodes,
)
from models.group_model import Group

logger = logging.getLogger(__name__)

load_dotenv()
redis_conn = Redis(decode_responses=True, host="redis")
task_queue = Queue(connection=redis_conn)


class HttpMethod(Enum):
    post = "post"
    delete = "delete"
    get = "get"


class ClusterAPIConsumer:
    def __init__(self):
        self.hosts = Config().get_hosts()
        self.endpoint_group = "/v1/group"

    async def create_group(self, group_id: str) -> bool:
        successfully_created_hosts: List[str] = []
        for host in self.hosts:
            response = await self._make_request(
                method=HttpMethod.post, host=host, group_id=group_id
            )
            if response and response.status_code == httpx.codes.CREATED:
                successfully_created_hosts.append(host)
                logger.info(f"Group '{group_id}' created on host '{host}'")

            else:
                get_response = await self._make_request(
                    method=HttpMethod.get, host=host, group_id=group_id
                )
                if get_response and get_response.status_code == httpx.codes.OK:
                    logger.warning(
                        f"Group '{group_id}' already exists on host '{host}'"
                    )
                    raise GroupAlreadyExistsException()
                else:
                    await self._rollback_created_groups(
                        group_id, successfully_created_hosts
                    )
                    logger.error(
                        f"Failed to create group '{group_id}' on host '{host}'"
                    )
                    raise FailedToCreateGroupInAllNodes()
        return True

    async def delete_group(self, group_id: str) -> bool:
        successfully_deleted_hosts: List[str] = []
        for host in self.hosts:
            response = await self._make_request(
                method=HttpMethod.delete, host=host, group_id=group_id
            )
            if response and response.status_code == httpx.codes.OK:
                successfully_deleted_hosts.append(host)
                logger.info(f"Group '{group_id}' deleted from host '{host}'")

            else:
                await self._rollback_deleted_groups(
                    group_id, successfully_deleted_hosts
                )
                logger.error(f"Failed to delete group '{group_id}' from host '{host}'")
                raise FailedToDeleteGroupFromAllNodes()
        return True

    async def _make_request(
            self, method: HttpMethod, host: str, group_id: str
    ) -> httpx.Response | None:
        async with httpx.AsyncClient(trust_env=False) as async_client:
            url = f"http://{host.strip()}{self.endpoint_group}"
            try:
                if method == HttpMethod.post:
                    return await async_client.post(url, json={Group.GROUP_ID: group_id})
                elif method == HttpMethod.delete:
                    return await async_client.delete(
                        url, params={Group.GROUP_ID: group_id}
                    )
                elif method == HttpMethod.get:
                    return await async_client.get(
                        url, params={Group.GROUP_ID: group_id}
                    )
            except httpx.RequestError:
                logger.error(f"Unable to make {method} request to {url}")
            return None

    async def _rollback_created_groups(
            self, group_id: str, hosts_to_rollback: List[str]
    ):
        for host in hosts_to_rollback:
            response = await self._make_request(HttpMethod.delete, host, group_id)
            if not (response and response.status_code == httpx.codes.OK):
                logger.warning(f"Failed to rollback group creation on host '{host}'")
                task_queue.enqueue_in(
                    time_delta=timedelta(seconds=60),
                    func=self._rollback_created_groups,
                    args=(group_id, [host]),
                )

    async def _rollback_deleted_groups(
            self, group_id: str, hosts_to_rollback: List[str]
    ):
        for host in hosts_to_rollback:
            response = await self._make_request(HttpMethod.post, host, group_id)
            if not (response and response.status_code == httpx.codes.CREATED):
                task_queue.enqueue_in(
                    time_delta=timedelta(seconds=60),
                    func=self._rollback_created_groups,
                    args=(group_id, [host]),
                )
