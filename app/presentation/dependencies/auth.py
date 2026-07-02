from fastapi import Request


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
