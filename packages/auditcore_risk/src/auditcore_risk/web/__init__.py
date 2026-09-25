"""REST interface and display data for risk flags (extras ``web`` / ``fastapi``).

The handlers in :mod:`.service` and the profile descriptions in :mod:`.catalog`
need no web framework; :func:`create_app` (Starlette) and
:func:`build_fastapi_router` (FastAPI) bind them to HTTP. Contract:
``docs/ui/risk-rest.md`` in the auditcore repository.
"""

from .catalog import list_profiles, profile_detail, profile_fields, rule_parameters
from .http import MAX_BODY_BYTES, build_fastapi_router, create_app, routes
from .jsontypes import JsonObject, JsonValue, json_safe
from .service import (
    MAX_RECORDS,
    ApiError,
    Limits,
    handle_check_columns,
    handle_evaluate,
    handle_profile,
    handle_profiles,
    library_error,
)

__all__ = [
    "MAX_BODY_BYTES",
    "MAX_RECORDS",
    "ApiError",
    "JsonObject",
    "JsonValue",
    "Limits",
    "build_fastapi_router",
    "create_app",
    "handle_check_columns",
    "handle_evaluate",
    "handle_profile",
    "handle_profiles",
    "json_safe",
    "library_error",
    "list_profiles",
    "profile_detail",
    "profile_fields",
    "routes",
    "rule_parameters",
]
