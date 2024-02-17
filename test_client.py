import respx
from httpx import codes, Response, TimeoutException
from client import ClusterAPIConsumer


class TestClusterAPIConsumer:
    def setup_method(self):
        self.client = ClusterAPIConsumer()

    @staticmethod
    def create_group_success_response_mock():
        response = Response(
            status_code=codes.CREATED, json={"message": "Group created successfully"}
        )
        return response

    @staticmethod
    def create_bad_request_response_mock():
        response = Response(
            status_code=codes.BAD_REQUEST,
            json={"message": "Bad request. Perhaps the object exists."},
        )
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
    def test_success_create_group_with_respx(self):
        group_id = "example_group_id"
        routes = [
            respx.post(f"https://{host}{self.client.endpoint_group}").mock(
                return_value=self.create_group_success_response_mock()
            )
            for host in self.client.hosts
        ]

        result = self.client.create_group(group_id)
        assert result is True
        for route in routes:
            assert route.called
