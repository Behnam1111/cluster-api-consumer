import pytest
import respx
from httpx import codes, Response, TimeoutException

from client import ClusterAPIConsumer


@pytest.mark.asyncio
class TestClusterAPIConsumer:
    def setup_method(self):
        self.client = ClusterAPIConsumer()

    def _create_success_post_mock(self, endpoint: str, name: str):
        return respx.post(endpoint, name=name).mock(
            return_value=self._create_group_success_response()
        )

    def _create_failure_post_mock(self, endpoint: str, name: str):
        return respx.post(endpoint, name=name).mock(
            return_value=self._create_bad_request_response()
        )

    def _delete_success_mock(self, endpoint: str):
        mock = respx.delete(endpoint).mock(
            return_value=self._create_group_success_response()
        )
        return mock

    @staticmethod
    def _create_group_success_response():
        response = Response(
            status_code=codes.CREATED, json={"message": "Group created successfully"}
        )
        return response

    @staticmethod
    def _create_bad_request_response():
        response = Response(
            status_code=codes.BAD_REQUEST,
            json={"message": "Bad request. Perhaps the object exists."},
        )
        return response

    @staticmethod
    def _delete_group_success_response():
        response = Response(status_code=codes.OK)
        return response

    @staticmethod
    def mock_success_delete_response():
        response = Response(
            status_code=codes.OK, json={"message": "Group deleted successfully"}
        )
        return response

    @staticmethod
    def mock_success_get_response(group_id: str):
        response = Response(status_code=codes.OK, json={"groupId": group_id})
        return response

    @staticmethod
    def mock_timeout_response():
        raise TimeoutException("Request timed out")

    @staticmethod
    def mock_internal_server_error_response():
        response = Response(status_code=codes.INTERNAL_SERVER_ERROR)
        return response

    @respx.mock
    async def test_success_create_group(self):
        group_id = "example_group_id"
        routes = [
            self._create_success_post_mock(
                endpoint=f"https://{host}{self.client.endpoint_group}", name=host
            )
            for host in self.client.hosts
        ]

        result = await self.client.create_group(group_id)
        assert result is True
        for route in routes:
            assert route.called

    @respx.mock
    async def test_failure_create_group(self):
        group_id = "example_group_id"
        routes = [
            self._create_success_post_mock(
                endpoint=f"https://{self.client.hosts[0]}{self.client.endpoint_group}",
                name=self.client.hosts[0],
            ),
            self._create_success_post_mock(
                endpoint=f"https://{self.client.hosts[1]}{self.client.endpoint_group}",
                name=self.client.hosts[1],
            ),
            self._create_failure_post_mock(
                endpoint=f"https://{self.client.hosts[2]}{self.client.endpoint_group}",
                name=self.client.hosts[2],
            ),
        ]
        for host in self.client.hosts:
            self._delete_success_mock(
                endpoint=f"https://{host}{self.client.endpoint_group}?groupId={group_id}",
            )

        result = await self.client.create_group(group_id)
        assert result is False
        for route in routes:
            assert route.called
