from typing import List
from pydantic import BaseModel, Field


class FoodResponse(BaseModel):
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

    nutrition_info: List[dict] = Field(
        default_factory=list,
        description="Nutritional information for the identified ingredients from the database."
    )

    filename: str = Field(
        ...,
        description="Name of the uploaded image."
    )

    device: str = Field(
        ...,
        description="Device the model ran on (cuda, mps, or cpu)."
    )
