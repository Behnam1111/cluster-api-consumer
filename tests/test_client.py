import respx
import pytest
from httpx import codes, Response

from client import ClusterAPIConsumer, FailedToCreateGroupInAllNodes, GroupAlreadyExistsException
from exceptions.custom_exceptions import FailedToDeleteGroupFromAllNodes


@pytest.mark.asyncio
class TestClusterAPIConsumer:
    def setup_method(self):
        self.client = ClusterAPIConsumer()
        self.group_id = "example_group_id"

    @staticmethod
    def _create_post_mock(endpoint: str, status_code: int, json=None):
        response = Response(status_code=status_code, json=json)
        return respx.post(endpoint).mock(return_value=response)

    @staticmethod
    def _get_post_mock(endpoint: str, status_code: int):
        response = Response(status_code=status_code)
        return respx.get(endpoint).mock(return_value=response)

    @staticmethod
    def _delete_mock(endpoint: str, status_code: int):
        response = Response(status_code=status_code)
        return respx.delete(endpoint).mock(return_value=response)

    @respx.mock
    async def test_success_create_group(self):
        with respx.mock:
            for host in self.client.hosts:
                self._create_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}",
                    status_code=codes.CREATED,
                    json={"message": "Group created successfully"},
                )
            result = await self.client.create_group(self.group_id)
            assert result is True

    @respx.mock
    async def test_failure_create_group(self):
        with respx.mock:
            for host in self.client.hosts[:2]:
                self._create_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}",
                    status_code=codes.CREATED,
                    json={"message": "Group created successfully"},
                )
            self._create_post_mock(
                endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}",
                status_code=codes.INTERNAL_SERVER_ERROR,
            )

            self._get_post_mock(
                endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}",
                status_code=codes.NOT_FOUND,
            )

            for host in self.client.hosts:
                self._delete_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}?groupId={self.group_id}",
                    status_code=codes.OK,
                )
            with pytest.raises(FailedToCreateGroupInAllNodes):
                result = await self.client.create_group(self.group_id)
                assert result is False

    @respx.mock
    async def test_success_delete_group(self):
        with respx.mock:
            for host in self.client.hosts:
                self._delete_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}?groupId={self.group_id}",
                    status_code=codes.OK,
                )
            result = await self.client.delete_group(self.group_id)
            assert result is True

    @respx.mock
    async def test_failure_delete_group(self):
        with respx.mock:
            for host in self.client.hosts[:2]:
                self._delete_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}?groupId={self.group_id}",
                    status_code=codes.OK,
                )
            self._delete_mock(
                endpoint=f"http://{self.client.hosts[2]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.INTERNAL_SERVER_ERROR,
            )

            for host in self.client.hosts:
                self._create_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}",
                    status_code=codes.CREATED,
                    json={"message": "Group created successfully"},
                )

            with pytest.raises(FailedToDeleteGroupFromAllNodes):
                result = await self.client.delete_group(self.group_id)
                assert result is False

    @respx.mock
    async def test_success_group_id_already_exists(self):
        with respx.mock:
            for host in self.client.hosts:
                self._create_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}",
                    status_code=codes.BAD_REQUEST,
                    json={"message": "Bad request. Perhaps the object exists."},
                )

            self._get_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.OK,
            )

            with pytest.raises(GroupAlreadyExistsException):
                result = await self.client.create_group(self.group_id)
                assert result is not True

    @respx.mock
    async def test_failure_group_id_not_exists(self):
        with respx.mock:
            for host in self.client.hosts:
                self._create_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}",
                    status_code=codes.BAD_REQUEST,
                    json={"message": "Bad request. Perhaps the object exists."},
                )
            self._get_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.NOT_FOUND,
            )
            with pytest.raises(FailedToCreateGroupInAllNodes):
                result = await self.client.create_group(self.group_id)
                assert result is False


    @respx.mock
    async def test_rollback_on_unsuccessful_group_creation(self):
        with respx.mock:
            self._create_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}",
                status_code=codes.CREATED
            )
            self._create_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}",
                status_code=codes.CREATED
            )
            self._create_post_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}",
                status_code=codes.INTERNAL_SERVER_ERROR
            )
            self._delete_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.INTERNAL_SERVER_ERROR
            )

            self._delete_mock(
                endpoint=f"http://{self.client.hosts[1]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.OK
            )
            for host in self.client.hosts:
                self._get_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}?groupId={self.group_id}",
                    status_code=codes.NOT_FOUND
                )

            with pytest.raises(FailedToCreateGroupInAllNodes):
                result = await self.client.create_group(self.group_id)
                assert result is False

    @respx.mock
    async def test_rollback_on_unsuccessful_group_deletion(self):
        with respx.mock:
            self._delete_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.OK
            )
            self._delete_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.OK
            )
            self._delete_mock(
                endpoint=f"http://{self.client.hosts[0]}{self.client.endpoint_group}?groupId={self.group_id}",
                status_code=codes.INTERNAL_SERVER_ERROR
            )

            for host in self.client.hosts:
                self._create_post_mock(
                    endpoint=f"http://{host}{self.client.endpoint_group}",
                    status_code=codes.INTERNAL_SERVER_ERROR
                )

            with pytest.raises(FailedToDeleteGroupFromAllNodes):
                result = await self.client.delete_group(self.group_id)
                assert result is False
