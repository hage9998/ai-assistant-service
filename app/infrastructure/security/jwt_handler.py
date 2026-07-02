from typing import TypedDict


class JwtPayload(TypedDict):
    """Expected JWT payload format, equivalent to NestJS's `JwtPayload`."""

    sub: str
    email: str
    name: str
