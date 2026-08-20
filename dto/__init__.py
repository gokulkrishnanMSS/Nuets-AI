"""Deprecated: this package moved to :mod:`schemas`.

Kept so existing ``from dto...`` imports keep working. New code should import
from ``schemas.food`` / ``schemas.recipe`` instead.
"""

import warnings

from schemas import (  # noqa: F401
    DEFAULT_PROMPT,
    EXAMPLE_DESCRIPTION,
    FoodRequest,
    FoodResponse,
    RecipeIngredient,
    RecipeRequest,
    RecipeResponse,
    RecipeStep
)

warnings.warn(
    "`dto` is deprecated, import from `schemas` instead "
    "(e.g. `from schemas.recipe import RecipeRequest`).",
    DeprecationWarning,
    stacklevel=2
)

__all__ = [
    "DEFAULT_PROMPT",
    "EXAMPLE_DESCRIPTION",
    "FoodRequest",
    "FoodResponse",
    "RecipeRequest",
    "RecipeIngredient",
    "RecipeStep",
    "RecipeResponse"
]
