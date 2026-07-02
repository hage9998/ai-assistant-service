from typing import TypedDict

from jose import ExpiredSignatureError, JWTError, jwt

from app.domain.exceptions.domain_exceptions import InvalidTokenException
from app.infrastructure.config.settings import Settings


class JwtPayload(TypedDict):
    """Expected format of the JWT payload."""

    sub: str
    email: str
    name: str


def decode_token(token: str, settings: Settings) -> JwtPayload:
    """Decodes and validates the JWT, returning the typed payload.

    - validates signature and expiration (done by the `jose` lib itself);
    - ensures `sub` and `email` are present in the payload.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except ExpiredSignatureError as exc:
        raise InvalidTokenException("Authentication token expired.") from exc
    except JWTError as exc:
        raise InvalidTokenException("Invalid authentication token.") from exc

    sub = payload.get("sub")
    email = payload.get("email")
    name = payload.get("name", "")

    if not sub or not email:
        raise InvalidTokenException(
            "Invalid token payload: 'sub' and 'email' fields are required."
        )

    return JwtPayload(sub=sub, email=email, name=name)
