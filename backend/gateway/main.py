from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os 

from gateway.routers import root, healthcheck, upload_file

app = FastAPI(title="Meeting Summarization Gateway")

# TODO: CONFIG Properly CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGINS", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# add router
app.include_router(root.router)
app.include_router(healthcheck.router)
app.include_router(upload_file.routers)