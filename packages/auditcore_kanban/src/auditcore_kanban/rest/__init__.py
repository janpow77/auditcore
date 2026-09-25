"""REST contract: framework-free handler plus optional Starlette/FastAPI adapters."""

from .api import METHODS, ROUTES, ApiResponse, KanbanApi
from .handlers import ApiRequest

__all__ = ["METHODS", "ROUTES", "ApiRequest", "ApiResponse", "KanbanApi"]
