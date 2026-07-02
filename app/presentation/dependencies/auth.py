from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.domain.entities.user import CurrentUser
from app.domain.exceptions.domain_exceptions import (
    InvalidTokenException,
    MissingTokenException,
)
from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.security.jwt_handler import decode_token


def _extract_token_from_request(request: Request) -> str:
    """Extract the JWT from the request headers or cookies.

    Priority order is the same as configured in the `JwtStrategy` of NestJS:
    1. Authorization: Bearer <token>
    2. Cookie `accessToken`
    3. Cookie `token`
    """
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            return token

    cookie_token = request.cookies.get("accessToken") or request.cookies.get("token")
    if cookie_token:
        return cookie_token

    raise MissingTokenException


async def get_current_user(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> CurrentUser:
    """FastAPI dependency that returns the authenticated user from the request."""
    try:
        token = _extract_token_from_request(request)
        payload = decode_token(token, settings)
    except (MissingTokenException, InvalidTokenException) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return CurrentUser(
        id=payload["sub"],
        email=payload["email"],
        name=payload.get("name", ""),
    )
