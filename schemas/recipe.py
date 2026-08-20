from typing import List, Optional

from pydantic import Field

from schemas.base import BaseSchema

EXAMPLE_DESCRIPTION = (
    "A spicy South Indian chicken biryani with basmati rice and yogurt marinade."
)


class RecipeRequest(BaseSchema):
    """Body accepted by POST /recipe/generate."""

    description: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Description of the dish you want a preparation procedure for.",
        examples=[EXAMPLE_DESCRIPTION]
    )

    servings: int = Field(
        default=2,
        ge=1,
        le=20,
        description="Number of servings the recipe should yield."
    )

    dietary_preference: Optional[str] = Field(
        default=None,
        max_length=200,
        description=(
            "Optional dietary constraint to respect, e.g. 'vegan', "
            "'gluten-free', 'no dairy', 'low sodium'."
        ),
        examples=["gluten-free"]
    )

    max_new_tokens: int = Field(
        default=1536,
        ge=256,
        le=4096,
        description="Maximum number of tokens to generate for the recipe."
    )


class RecipeIngredient(BaseSchema):
    """A single ingredient line of the recipe."""

    item: str = Field(
        ...,
        description="Name of the ingredient."
    )

    quantity: str = Field(
        default="",
        description="Amount needed for the given number of servings, e.g. '200 g'."
    )

    notes: str = Field(
        default="",
        description="Preparation note or healthier substitution, e.g. 'use brown rice'."
    )


class RecipeStep(BaseSchema):
    """A single step of the preparation procedure."""

    step_number: int = Field(
        ...,
        description="Order of the step in the procedure, starting at 1."
    )

    instruction: str = Field(
        ...,
        description="What to do in this step."
    )

    duration_minutes: Optional[int] = Field(
        default=None,
        description="Approximate time this step takes, in minutes."
    )


class RecipeResponse(BaseSchema):
    """Healthy preparation procedure generated from a food description."""

    dish_name: str = Field(
        ...,
        description="Name of the dish derived from the description."
    )

    summary: str = Field(
        default="",
        description="Short description of the healthy version of the dish."
    )

    servings: int = Field(
        ...,
        description="Number of servings this recipe yields."
    )

    prep_time_minutes: int = Field(
        default=0,
        description="Hands-on preparation time in minutes."
    )

    cook_time_minutes: int = Field(
        default=0,
        description="Cooking time in minutes."
    )

    total_time_minutes: int = Field(
        default=0,
        description="Total time from start to serving, in minutes."
    )

    ingredients: List[RecipeIngredient] = Field(
        default_factory=list,
        description="Ingredients required, with quantities for the requested servings."
    )

    steps: List[RecipeStep] = Field(
        default_factory=list,
        description="Ordered preparation and cooking steps."
    )

    health_notes: List[str] = Field(
        default_factory=list,
        description="What makes this preparation healthier, and healthier swaps used."
    )

    # Free-form so a model that reports extra nutrients is not rejected.
    nutrition_estimate: dict = Field(
        default_factory=dict,
        description="Rough per-serving estimate: calories, protein_g, carbs_g, fat_g, fiber_g."
    )

    device: str = Field(
        ...,
        description="Device the model ran on (cuda, mps, or cpu)."
    )

    raw_output: Optional[str] = Field(
        default=None,
        description="Raw model text, returned only when the structured parse was incomplete."
    )
