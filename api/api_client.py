import logging

from fastapi import APIRouter, Depends, status

from models.group_model import Group
from client import ClusterAPIConsumer

logger = logging.getLogger(__name__)
router = APIRouter()


def get_cluster_api_consumer():
    return ClusterAPIConsumer()


@router.post("/v1/group", status_code=status.HTTP_201_CREATED)
async def create_group(
    group: Group, client: ClusterAPIConsumer = Depends(get_cluster_api_consumer)
):
    result = await client.create_group(group.group_id)
    if result:
        return {"groupId": group.group_id}


@router.delete("/v1/group/{group_id}", status_code=status.HTTP_200_OK)
async def delete_group(
    group_id: str, client: ClusterAPIConsumer = Depends(get_cluster_api_consumer)
):
    result = await client.delete_group(group_id)
    if result:
        return {"groupId": group_id}
