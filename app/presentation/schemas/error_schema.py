from pydantic import BaseModel


class ErrorResponseSchema(BaseModel):
    """Standardized error format returned by the API."""

    error_code: str
    detail: str
