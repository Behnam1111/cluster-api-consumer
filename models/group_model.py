from pydantic import BaseModel


class Group(BaseModel):
    GROUP_ID: str = "groupId"
    group_id: str
