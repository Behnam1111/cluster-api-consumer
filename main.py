from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from api import cluster_gateway
from exceptions.custom_exceptions import GroupAlreadyExistsException, FailedToCreateGroupInAllNodes, \
    FailedToDeleteGroupFromAllNodes
from utils.logger import setup_logging

setup_logging()
app = FastAPI()

app.include_router(cluster_gateway.router, prefix="/client")


@app.exception_handler(GroupAlreadyExistsException)
async def group_already_exists_handler(request: Request,
                                       exc: GroupAlreadyExistsException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.debug_message}
    )


@app.exception_handler(FailedToCreateGroupInAllNodes)
async def failed_to_create_group_in_all_nodes(request: Request,
                                              exc: FailedToCreateGroupInAllNodes):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.debug_message}
    )


@app.exception_handler(FailedToCreateGroupInAllNodes)
async def failed_to_delete_group_from_all_nodes(request: Request,
                                                exc: FailedToDeleteGroupFromAllNodes):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.debug_message}
    )
