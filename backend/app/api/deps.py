"""API dependencies."""
from fastapi import Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.simulation.microgrid_engine import engine


def get_engine():
    """Get microgrid engine instance."""
    return engine


def get_client_ip(request: Request) -> str:
    """Get client IP address."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
