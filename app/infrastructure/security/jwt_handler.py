from typing import TypedDict

from jose import ExpiredSignatureError, JWTError, jwt

from app.domain.exceptions.domain_exceptions import InvalidTokenException
from app.infrastructure.config.settings import Settings


class JwtPayload(TypedDict):
    """Expected JWT payload format, equivalent to NestJS's `JwtPayload`."""

    sub: str
    email: str
    name: str


def decode_token(token: str, settings: Settings) -> JwtPayload:
    """Decode and validate the JWT, returning the typed payload.

    Equivalent to NestJS's `JwtStrategy.validate()` method:
    - validates signature and expiration (done by the `jose` lib itself);
    - ensures `sub` and `email` are present in the payload.
    """
