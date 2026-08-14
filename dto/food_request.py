from fastapi import UploadFile
from pydantic import BaseModel, Field

DEFAULT_PROMPT = "Identify this food and describe it."


class FoodRequest(BaseModel):
    image: UploadFile = Field(
        ...,
        description="The image file to analyse (jpeg, png, webp, ...)."
    )

    prompt: str = Field(
        default=DEFAULT_PROMPT,
        description="Instruction sent to the vision-language model.",
        examples=[DEFAULT_PROMPT]
    )

    max_new_tokens: int = Field(
        default=64,
        ge=1,
        le=1024,
        description="Maximum number of tokens to generate."
    )
