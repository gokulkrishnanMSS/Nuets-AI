from pydantic import BaseModel, Field


class FoodResponse(BaseModel):
    result: str = Field(
        ...,
        description="The model's answer."
    )

    filename: str = Field(
        ...,
        description="Name of the uploaded image."
    )

    device: str = Field(
        ...,
        description="Device the model ran on (mps or cpu)."
    )
