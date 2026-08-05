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


class MissingTokenException(DomainException):
    """Raised when no token is found in the request."""

    error_code = "missing_token"
    message = "Authentication token not found."


class LLMProviderException(DomainException):
    """Raised when a communication failure with the LLM provider occurs."""

    error_code = "llm_provider_error"
    message = "Failed to communicate with the language provider (LLM)."


class McpClientException(DomainException):
    """Raised when a communication failure with the MCP service occurs."""

    error_code = "mcp_client_error"
    message = "Failed to communicate with the MCP service."
