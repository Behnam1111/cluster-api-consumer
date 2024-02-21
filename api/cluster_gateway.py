from models.models import Group
from client import ClusterAPIConsumer
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()


def get_cluster_api_consumer():
    return ClusterAPIConsumer()


@router.post("/v1/group", status_code=status.HTTP_201_CREATED)
async def create_group(
    group: Group, client: ClusterAPIConsumer = Depends(get_cluster_api_consumer)
):
    if await client.create_group(group.group_id):
        return {"group_id": group.group_id}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create group"
    )


@router.delete("/v1/group/{group_id}", status_code=status.HTTP_200_OK)
async def delete_group(
    group_id: str, client: ClusterAPIConsumer = Depends(get_cluster_api_consumer)
):
    if await client.delete_group(group_id):
        return {"group_id": group_id}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete group"
    )
