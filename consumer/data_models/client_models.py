from enum import Enum


class HttpMethod(Enum):
    post = "post"
    delete = "delete"
    get = "get"


class Group:
    GROUP_ID = "groupId"
