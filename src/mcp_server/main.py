"""
Compatibility module exposing the FastAPI application entrypoint.
"""
from mcp_server.adapters.http.main import app

__all__ = ["app"]


