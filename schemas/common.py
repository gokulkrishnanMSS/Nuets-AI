from pydantic import Field

from schemas.base import BaseSchema


class ErrorResponse(BaseSchema):
    """Body returned by FastAPI for a raised HTTPException."""

    detail: str = Field(
        ...,
        description="Human readable explanation of what went wrong.",
        examples=["Could not read the uploaded image: cannot identify image file"]
    )
