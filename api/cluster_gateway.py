from models.models import Group
import logging
from client import ClusterAPIConsumer
from fastapi import APIRouter, Depends, status

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
        return {Group.GROUP_ID: group.group_id}


@router.delete("/v1/group/{group_id}", status_code=status.HTTP_200_OK)
async def delete_group(
    group_id: str, client: ClusterAPIConsumer = Depends(get_cluster_api_consumer)
):
    result = await client.delete_group(group_id)
    if result:
        return {Group.GROUP_ID: group_id}
