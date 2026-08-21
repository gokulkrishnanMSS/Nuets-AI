from typing import List

from fastapi import UploadFile
from pydantic import Field

from schemas.base import BaseSchema

DEFAULT_PROMPT = "Identify this food and describe it."


class FoodRequest(BaseSchema):
    """Multipart form accepted by POST /food/identify."""

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


class FoodResponse(BaseSchema):
    """Result of identifying the food in an uploaded image."""

    result: str = Field(
        ...,
        description="The model's identification/description of the food."
    )

    ingredients: List[str] = Field(
        default_factory=list,
        description="List of ingredients detected in or required for the dish.",
        examples=[[
            "pizza dough",
            "tomato sauce",
            "mozzarella cheese",
            "pepperoni",
            "oregano"
        ]]
    )

    # Rows come straight from the nutrition_data table, whose columns can grow,
    # so these stay untyped dicts rather than a fixed schema.
    nutrition_info: List[dict] = Field(
        default_factory=list,
        description="Nutritional information for the identified ingredients from the database."
    )

    calories_kcal: float = Field(
        ...,
        description=(
            "Calories of the food shown, in kcal, as estimated by the model. "
            "A best-effort estimate from the image alone, not a measurement."
        ),
        examples=[850.0]
    )

    filename: str = Field(
        ...,
        description="Name of the uploaded image."
    )

    device: str = Field(
        ...,
        description="Device the model ran on (cuda, mps, or cpu)."
    )
