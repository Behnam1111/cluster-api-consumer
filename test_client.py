import httpx

from client import ClusterAPIConsumer


class TestClusterAPIConsumer:
    def setup_method(self):
        self.client = ClusterAPIConsumer()

    @staticmethod
    def mock_success_create_response():
        response = httpx.Response(
            status_code=201, json={"message": "Group created successfully"}
        )
        return response

    @staticmethod
    def mock_bad_request_create_response():
        response = httpx.Response(
            status_code=400, json={"message": "Bad request. Perhaps the object exists."}
        )
        return response

    @staticmethod
    def mock_success_delete_response():
        response = httpx.Response(
            status_code=200, json={"message": "Group deleted successfully"}
        )
        return response

    @staticmethod
    def mock_success_get_response(group_id: str):
        response = httpx.Response(status_code=200, json={"groupId": group_id})
        return response

    @staticmethod
    def mock_timeout_response():
        raise httpx.TimeoutException("Request timed out")

    @staticmethod
    def mock_internal_server_error_response():
        response = httpx.Response(status_code=500)
        return response

    def test_success_create_group(self, monkeypatch):
        group_id = "example_group"

        def mock_post():
            return self.mock_success_create_response()

        monkeypatch.setattr(httpx, "post", mock_post)
        result = self.client.create_group(group_id)
        assert result is True
        for host in self.client.hosts:
            assert httpx.post(f"http://{host}/v1/group/", json={"groupId": group_id})
