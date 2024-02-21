import respx
import pytest
from httpx import codes, Response

from client import ClusterAPIConsumer


@pytest.mark.asyncio
class TestClusterAPIConsumer:
    def setup_method(self):
        self.client = ClusterAPIConsumer()
        self.group_id = "example_group_id"

    def _create_success_post_mock(self, endpoint: str):
        return respx.post(endpoint).mock(
            return_value=self._create_group_success_response()
        )

    def _create_bad_request_post_mock(self, endpoint: str):
        return respx.post(endpoint).mock(
            return_value=self._create_bad_request_response()
        )

    def _create_internal_server_error_mock(self, endpoint: str):
        return respx.post(endpoint).mock(
            return_value=self._create_internal_server_error_response()
        )

    def _get_success_post_mock(self, endpoint: str):
        return respx.get(endpoint).mock(
            return_value=self._get_success_group_response()
        )

    def _get_not_found_post_mock(self, endpoint: str):
        return respx.get(endpoint).mock(
            return_value=self._get_not_found_group_response()
        )

    def _delete_success_mock(self, endpoint: str):
        mock = respx.delete(endpoint).mock(
            return_value=self._delete_group_success_response()
        )
        return mock

    def _delete_failure_mock(self, endpoint: str):
        mock = respx.delete(endpoint).mock(
            return_value=self._internal_server_error_failure_response()
        )
        return mock

    @staticmethod
    def _create_group_success_response():
        response = Response(
            status_code=codes.CREATED, json={"message": "Group created successfully"}
        )
        return response

    @staticmethod
    def _get_success_group_response():
        response = Response(
            status_code=codes.OK
        )
        return response

    @staticmethod
    def _get_not_found_group_response():
        response = Response(
            status_code=codes.NOT_FOUND
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
    def _create_internal_server_error_response():
        response = Response(
            status_code=codes.INTERNAL_SERVER_ERROR,
        )
        return response

    @staticmethod
    def _delete_group_success_response():
        response = Response(status_code=codes.OK)
        return response

    @staticmethod
    def _internal_server_error_failure_response():
        response = Response(status_code=codes.INTERNAL_SERVER_ERROR)
        return response

    @respx.mock
    async def test_success_create_group(self):
        with respx.mock:
            group_id = "example_group_id"
            routes = [
                self._create_success_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}"
                )
                for host in self.client.hosts
            ]

            result = await self.client.create_group(group_id)
            assert result is True
            for route in routes:
                assert route.called

    @respx.mock
    async def test_failure_create_group(self):
        with respx.mock:
            routes = [
                self._create_success_post_mock(
                    endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}",
                ),
                self._create_success_post_mock(
                    endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}",
                ),
                self._create_internal_server_error_mock(
                    endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}",
                ),
            ]

            self._get_success_post_mock(
                endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}",
            )

            for host in self.client.hosts:
                self._delete_success_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}?groupId={self.group_id}",
                )

            result = await self.client.create_group(self.group_id)
            assert result is False
            for route in routes:
                assert route.called

    @respx.mock
    async def test_success_delete_group(self):
        with respx.mock:
            routes = [
                self._delete_success_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}?groupId={self.group_id}",
                )
                for host in self.client.hosts
            ]

            result = await self.client.delete_group(self.group_id)
            assert result is True
            for route in routes:
                assert route.called

    @respx.mock
    async def test_failure_delete_group(self):
        with respx.mock:
            routes = [
                self._delete_success_mock(
                    endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                ),
                self._delete_success_mock(
                    endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}?groupId={self.group_id}",
                ),
                self._delete_failure_mock(
                    endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}?groupId={self.group_id}",
                ),
            ]
            for host in self.client.hosts:
                self._create_success_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}",
                )

            result = await self.client.delete_group(self.group_id)
            assert result is False

    @respx.mock
    async def test_success_group_id_already_exists(self):
        with respx.mock:
            [
                self._create_bad_request_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}"
                )
                for host in self.client.hosts
            ]

            self._get_success_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
            )

            result = await self.client.create_group(self.group_id)
            assert result is False

    @respx.mock
    async def test_failure_group_id_not_exists(self):
        with respx.mock:
            [
                self._create_bad_request_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}"
                )
                for host in self.client.hosts
            ]
            self._get_not_found_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
            )

            result = await self.client.create_group(self.group_id)
            assert result is False

    @respx.mock
    async def test_rollback_on_unsuccessful_group_creation(self, mocker):
        with respx.mock:
            self._create_success_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}",
            )
            self._create_success_post_mock(
                endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}",
            )
            self._create_internal_server_error_mock(
                endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}",
            )

            self._delete_failure_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}"
            )

            self._delete_success_mock(
                endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}?groupId={self.group_id}"
            )

            self._get_not_found_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
            )

            self._get_not_found_post_mock(
                endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}?groupId={self.group_id}",
            )

            self._get_not_found_post_mock(
                endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}?groupId={self.group_id}",
            )
            
            result = await self.client.create_group(self.group_id)
            assert result is False


    @respx.mock
    async def test_rollback_on_unsuccessful_group_deletion(self, mocker):
        with respx.mock:
            routes = [
                self._delete_success_mock(
                    endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                ),
                self._delete_success_mock(
                    endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}?groupId={self.group_id}",
                ),
                self._delete_failure_mock(
                    endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}?groupId={self.group_id}",
                ),
            ]
            self._create_internal_server_error_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}",
            )
            self._create_internal_server_error_mock(
                endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}",
            )
            self._create_internal_server_error_mock(
                endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}",
            )

            result = await self.client.delete_group(self.group_id)
            assert result is False
