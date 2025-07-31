"""
Gateway Service Schemas Module

This module defines the Pydantic models for the API Gateway Service,
used for input validation and response serialization.

Models:
    - ServiceStatus: Captures health and status information for downstream microservices.

Fields:
    - service (str): Name of the microservice.
    - status (str): Health status indicator (e.g., "healthy", "unhealthy").
    - message (str, optional): Additional details or error message (default: empty string).
"""
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    service: str
    status: str
    message: str = ""  # Optional detailed message or error information
