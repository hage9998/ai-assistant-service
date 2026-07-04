"""Pydantic (response) schema for the daily advice endpoint."""
from pydantic import BaseModel, Field


class AdviceResponseSchema(BaseModel):
    """Response body for the `GET /advice/daily` endpoint."""

    message: str = Field(
        ...,
        description="Medieval/mythical advice generated to motivate the user.",
        examples=[
            "Young adventurer, no sword becomes legendary without "
            "first facing countless battles."
        ],
    )
