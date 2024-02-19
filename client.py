import os
import httpx
import logging
import asyncio
import argparse
from typing import List
from typing import Optional
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        """Create a group across all hosts."""
        responses: List[httpx.Response] = []
        async with httpx.AsyncClient() as client:
            for host in self.hosts:
                response = await self.make_request(client, "post", host, group_id)
                if not response or response.status_code != httpx.codes.CREATED:
                    await self.rollback_created_groups(group_id, responses)
                    return False
                responses.append(response)
        return True

    async def delete_group(self, group_id: str) -> bool:
        """Delete a group across all hosts."""
        responses: List[httpx.Response] = []
        async with httpx.AsyncClient() as client:
            for host in self.hosts:
                response = await self.make_request(client, "delete", host, group_id)
                if not response or response.status_code != httpx.codes.OK:
                    await self.rollback_deleted_groups(group_id, responses)
                    return False
                responses.append(response)
        return True

    async def make_request(
        self, client: httpx.AsyncClient, method: str, host: str, group_id: str
    ) -> Optional[httpx.Response]:
        """Helper method to make a request to the API."""
        url = f"https://{host.strip()}{self.endpoint_group}"
        try:
            if method == "post":
                return await client.post(url, json={"groupId": group_id})
            elif method == "delete":
                return await client.delete(url, params={"groupId": group_id})
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
        return None

    async def rollback_created_groups(
        self, group_id: str, responses: List[httpx.Response]
    ):
        """Rollback group creation in case of failure."""
        async with httpx.AsyncClient() as client:
            for response in responses:
                if response and response.status_code == httpx.codes.CREATED:
                    await self.make_request(
                        client, "delete", response.request.url.host, group_id
                    )

    async def rollback_deleted_groups(
        self, group_id: str, responses: List[httpx.Response]
    ):
        """Rollback group deletion in case of failure."""
        async with httpx.AsyncClient() as client:
            for response in responses:
                if response and response.status_code == httpx.codes.OK:
                    await self.make_request(
                        client, "post", response.request.url.host, group_id
                    )

    def get_group_by_id(self, host: str, group_id: str) -> Optional[dict]:
        """Retrieve group details by ID."""
        try:
            with httpx.Client() as client:
                response = client.get(f"https://{host}{self.endpoint_group}/{group_id}")
                if response.status_code == httpx.codes.OK:
                    return response.json()
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Cluster API Consumer")
    parser.add_argument(
        "action",
        choices=["create", "delete"],
        help="Action to perform: create or delete",
    )
    parser.add_argument("group_id", type=str, help="Group ID")
    args = parser.parse_args()

    consumer = ClusterAPIConsumer()

    action_map = {"create": consumer.create_group, "delete": consumer.delete_group}

    action_func = action_map.get(args.action)
    if action_func:
        result = asyncio.run(action_func(args.group_id))
        if result:
            logger.info(f"Group '{args.group_id}' {args.action}d successfully.")
        else:
            logger.error(f"Failed to {args.action} group '{args.group_id}'.")


if __name__ == "__main__":
    main()
