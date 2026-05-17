"""WebSocket JWT verification — see hr-interview-agent/src/auth.py for design notes."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from fastapi import Query, WebSocket, status
from jose import JWTError, jwt

logger = logging.getLogger(__name__)

JWT_PUBLIC_KEY_PATH = os.getenv("JWT_PUBLIC_KEY_PATH", "/app/keys/public.pem")
JWT_ALGORITHM = "RS256"
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
JWT_ISSUER = os.getenv("JWT_ISSUER")


@lru_cache(maxsize=1)
def _load_public_key() -> str:
    with open(JWT_PUBLIC_KEY_PATH, "r", encoding="utf-8") as f:
        return f.read()


class WebSocketAuthError(Exception):
    pass


def verify_ws_token(token: str) -> str:
    if not token:
        raise WebSocketAuthError("Missing token query parameter")
    try:
        payload = jwt.decode(
            token,
            _load_public_key(),
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"verify_aud": JWT_AUDIENCE is not None},
        )
    except JWTError as exc:
        raise WebSocketAuthError(f"Invalid token: {exc}") from exc

    user_id = payload.get("sub") or payload.get("user_id")
    if not user_id:
        raise WebSocketAuthError("Token does not contain a `sub` claim")
    return str(user_id)


async def authenticate_ws(
    websocket: WebSocket,
    token: str = Query(..., description="JWT issued by api-gateway"),
) -> str:
    try:
        return verify_ws_token(token)
    except WebSocketAuthError as exc:
        logger.warning("WebSocket auth rejected: %s", exc)
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=str(exc))
        raise
