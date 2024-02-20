from fastapi import FastAPI

from api import cluster_gateway

app = FastAPI()

app.include_router(cluster_gateway.router, prefix="/client")
