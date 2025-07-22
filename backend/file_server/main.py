from fastapi import FastAPI
from file_server.services import dowload, root, healthcheck

app = FastAPI(title="Meeting Summary File Server")

app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(dowload.router)
