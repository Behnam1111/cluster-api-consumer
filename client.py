import httpx
from httpx import Response
import os
from dotenv import load_dotenv

load_dotenv()


class ClusterAPIConsumer:
    def __init__(self):
        self.hosts = self._get_hosts()

    @staticmethod
    def _get_hosts():
        hosts_str = os.getenv("HOSTS")
        if hosts_str is None:
            raise ValueError("HOSTS environment variable not set")
        return hosts_str.split(",")

    def create_group(self, group_id: str) -> bool:
        responses = []
        for host in self.hosts:
            try:
                response = httpx.post(
                    f"http://{host}/v1/group/", json={"groupId": group_id}
                )
                responses.append(response)
            except httpx.RequestError as e:
                self.rollback_created_groups(group_id, responses)
                raise e
        return all(response.status_code == 201 for response in responses)

    def rollback_created_groups(self, group_id: str, responses: list[Response]):
        for response in responses:
            if response.status_code == 201:
                host = response.request.url.host
                httpx.delete(f"http://{host}/v1/group/")
