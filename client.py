import os
from typing import List

import httpx
from dotenv import load_dotenv
from httpx import Response, codes

load_dotenv()


class ClusterAPIConsumer:
    def __init__(self):
        self.hosts = self._get_hosts()
        self.endpoint_group = "/v1/group/"

    @staticmethod
    def _get_hosts():
        hosts_str = os.getenv("HOSTS")
        if hosts_str is None:
            raise ValueError("HOSTS environment variable not set")
        return hosts_str.split(",")

    def create_group(self, group_id: str) -> bool:
        responses: List[Response] = []
        with httpx.Client() as client:
            for host in self.hosts:
                try:
                    response = client.post(
                        url=f"https://{host}{self.endpoint_group}",
                        json={"groupId": group_id},
                    )

                    if response.status_code != httpx.codes.CREATED:
                        self.rollback_created_groups(group_id, responses)
                        return False

                    responses.append(response)

                except httpx.RequestError:
                    self.rollback_created_groups(group_id, responses)
                    raise

        return all(
            response.status_code == httpx.codes.CREATED for response in responses
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

    def rollback_created_groups(self, group_id: str, responses: list[Response]):
        with httpx.Client() as client:
            for response in responses:
                if response.status_code == codes.CREATED:
                    host = response.request.url.host
                    client.delete(
                        url=f"https://{host}{self.endpoint_group}",
                        params={"groupId": group_id},
                    )
