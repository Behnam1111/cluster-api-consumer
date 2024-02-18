import os
from typing import List

import httpx
from dotenv import load_dotenv
from httpx import Response, codes

load_dotenv()


def get_hosts() -> List[str]:
    hosts_str = os.getenv("HOSTS")
    if hosts_str is None:
        raise ValueError("HOSTS environment variable not set")
    return hosts_str.split(",")


class ClusterAPIConsumer:
    def __init__(self):
        self.hosts = get_hosts()
        self.endpoint_group = "/v1/group/"

    async def create_group(self, group_id: str) -> bool:
        responses: List[Response] = []
        async with httpx.AsyncClient() as client:
            for host in self.hosts:
                try:
                    response = await client.post(
                        url=f"https://{host}{self.endpoint_group}",
                        json={"groupId": group_id},
                    )
                    if response.status_code != httpx.codes.CREATED:
                        await self.rollback_created_groups(group_id, responses)
                        return False
                    responses.append(response)
                except httpx.RequestError:
                    await self.rollback_created_groups(group_id, responses)
                    raise
        return all(
            response.status_code == httpx.codes.CREATED for response in responses
        )

    async def delete_group(self, group_id: str) -> bool:
        responses: List[Response] = []
        async with httpx.AsyncClient() as client:
            for host in self.hosts:
                try:
                    response = await client.delete(
                        url=f"https://{host}{self.endpoint_group}",
                        params={"groupId": group_id},
                    )

                    if response.status_code != httpx.codes.OK:
                        await self.rollback_deleted_groups(group_id, responses)
                        return False
                    responses.append(response)
                except httpx.RequestError:
                    await self.rollback_deleted_groups(group_id, responses)
                    raise
        return all(response.status_code == httpx.codes.OK for response in responses)

    async def rollback_created_groups(self, group_id: str, responses: list[Response]):
        async with httpx.AsyncClient() as client:
            for response in responses:
                if response.status_code == codes.CREATED:
                    host = response.request.url.host
                    await client.delete(
                        url=f"https://{host}{self.endpoint_group}",
                        params={"groupId": group_id},
                    )

    async def rollback_deleted_groups(self, group_id: str, responses: list[Response]):
        async with httpx.AsyncClient() as client:
            for response in responses:
                if response.status_code == codes.OK:
                    host = response.request.url.host
                    await client.post(
                        url=f"https://{host}{self.endpoint_group}",
                        json={"groupId": group_id},
                    )

    def get_group_by_id(self, host: str, group_id: str):
        with httpx.Client() as client:
            try:
                response = client.get(
                    url=f"https://{host}{self.endpoint_group}/{group_id}"
                )
                return response.json()
            except httpx.RequestError:
                raise
