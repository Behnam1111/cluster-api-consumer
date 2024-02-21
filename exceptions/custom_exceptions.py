import logging


class DetailedException(Exception):
    status_code = 400

    def __init__(
        self,
        debug_message,
        status_code=None,
        payload=None,
        log_level: int = logging.ERROR,
    ):
        Exception.__init__(self)
        self.debug_message = debug_message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.log_level = log_level
        self.args = (debug_message,)


class GroupAlreadyExistsException(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            debug_message=message or "Group id already exists.",
            status_code=400,
        )


class FailedToCreateGroupInAllNodes(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            debug_message=message or "Failed to create group in all the nodes",
            status_code=400,
        )


class FailedToDeleteGroupFromAllNodes(DetailedException):
    def __init__(self, message=None):
        super().__init__(
            debug_message=message or "Failed to delete group from all nodes",
            status_code=400,
        )
