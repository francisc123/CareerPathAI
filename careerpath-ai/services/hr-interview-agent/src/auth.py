"""
WebSocket JWT verification for the HR interview agent.

WebSockets cannot carry custom Authorization headers reliably across browsers,
so the client must pass the token as a query string: `?token=...`.
We verify it with the RS256 public key mounted from the shared `keys/` volume.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from fastapi import Query, WebSocket, status
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "/app/keys/public.pem")
JWT_ALGORITHM = "RS256"
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")  # optional
JWT_ISSUER = os.getenv("JWT_ISSUER")  # optional


@lru_cache(maxsize=1)
def _load_public_key() -> str:
    try:
        with open(JWT_PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"JWT public key not found at {JWT_PUBLIC_KEY_PATH}. "
            "Run `make keys` and ensure the volume is mounted in docker-compose."
        ) from exc


class WebSocketAuthError(Exception):
    """Raised when WS auth fails. Caller is responsible for closing the socket."""


def verify_ws_token(token: str) -> str:
    """
    Verify a JWT for a WebSocket handshake. Returns the user_id (`sub` claim).
    Raises WebSocketAuthError on any failure.
    """
    if not token:
        raise WebSocketAuthError("Missing token query parameter")

    options = {"verify_aud": JWT_AUDIENCE is not None}
    try:
        payload = jwt.decode(
            token,
            _load_public_key(),
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options=options,
        )
    except JWTError as exc:
        raise WebSocketAuthError(f"Invalid token: {exc}") from exc

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise WebSocketAuthError("Token does not contain a `sub` / `user_id` claim")
    return str(user_id)


async def authenticate_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT issued by api-gateway"),
) -> str:
    """
    FastAPI dependency for WebSocket endpoints. Verifies the token and returns
    the authenticated user_id. On failure, closes the socket with policy
    violation (1008) and raises so the endpoint body does not run.
    """
    try:
        return verify_ws_token(token)
    except WebSocketAuthError as exc:
        logger.warning("WebSocket auth rejected: %s", exc)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
        raise
