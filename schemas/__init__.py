"""Pydantic request/response schemas for the Nuets Food AI Service.

One module per domain. Import from the domain module for clarity in new code::

    from schemas.recipe import RecipeRequest, RecipeResponse

The flat re-exports below exist so ``from schemas import RecipeRequest`` also
works.
"""

from schemas.base import BaseSchema
from schemas.common import ErrorResponse
from schemas.food import DEFAULT_PROMPT, FoodRequest, FoodResponse
from schemas.recipe import (
    EXAMPLE_DESCRIPTION,
    RecipeIngredient,
    RecipeRequest,
    RecipeResponse,
    RecipeStep
)

__all__ = [
    "BaseSchema",
    "ErrorResponse",
    "DEFAULT_PROMPT",
    "FoodRequest",
    "FoodResponse",
    "EXAMPLE_DESCRIPTION",
    "RecipeRequest",
    "RecipeIngredient",
    "RecipeStep",
    "RecipeResponse"
]
