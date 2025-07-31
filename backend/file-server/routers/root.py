"""
Root Endpoint
-------------

This module exposes the root (`/`) endpoint for the Meeting Summary File Server.

Used primarily to:
- Confirm the API is reachable.
- Provide a basic welcome/status message.
- Support quick curl-based checks or landing page logic.

Example response:
    {
        "message": "Meeting Summary File Server is live"
    }

Author: yodsran
"""

from fastapi import APIRouter

router = APIRouter(tags=["Root"])

@router.get("/")
def root():
    """
    Root service check endpoint.

    Returns:
        dict: A static message indicating that the server is running.
    """
    return {"message": "Meeting Summary File Server is live"}
