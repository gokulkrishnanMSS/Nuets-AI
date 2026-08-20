"""Deprecated: use :mod:`schemas.recipe` instead."""

from schemas.recipe import (  # noqa: F401
    RecipeIngredient,
    RecipeResponse,
    RecipeStep
)

__all__ = ["RecipeIngredient", "RecipeStep", "RecipeResponse"]
