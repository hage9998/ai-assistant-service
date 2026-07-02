class DomainException(Exception):
    """Base exception for all domain/application exceptions."""

    error_code: str = "domain_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class InvalidTokenException(DomainException):
    """Raised when the JWT is invalid, malformed, or expired."""

    error_code = "invalid_token"
    message = "Invalid authentication token."
