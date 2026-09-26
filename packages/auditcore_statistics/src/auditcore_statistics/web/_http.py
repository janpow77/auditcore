"""Framework-neutral request dispatch shared by the Starlette and FastAPI adapters."""

from __future__ import annotations

from decimal import Decimal

from auditcore_common.rest import Reply, decode_body, guarded, json_reply

from .analysis import ContractError, analyse, catalogue

MAX_BODY_BYTES = 64 * 1024 * 1024


def decode(raw: bytes, limit: int = MAX_BODY_BYTES) -> object:
    """JSON body with numbers as exact Decimal/int, within the size limit."""
    return decode_body(raw, limit, error=ContractError, parse_float=Decimal)


def profiles() -> Reply:
    """``GET /profiles``."""
    return json_reply(200, catalogue())


def handle_analyse(raw: bytes, limit: int = MAX_BODY_BYTES) -> Reply:
    """``POST /analyze`` with contract errors mapped to HTTP replies."""
    return guarded(lambda: json_reply(200, analyse(decode(raw, limit))), error=ContractError)
