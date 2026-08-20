from fastapi import APIRouter, HTTPException

from config.model_config import DEVICE
from schemas.common import ErrorResponse
from schemas.recipe import RecipeRequest, RecipeResponse
from service.recipe_service import RecipeService

router = APIRouter(
    prefix="/recipe",
    tags=["Recipe"]
)

recipe_service = RecipeService()


@router.post(
    "/generate",
    response_model=RecipeResponse,
    responses={
        500: {"model": ErrorResponse},
        502: {"model": ErrorResponse}
    },
    summary="Generate a healthy preparation procedure from a food description"
)
def generate_recipe(
    request: RecipeRequest
) -> RecipeResponse:

    try:

        recipe, raw_output = recipe_service.generate_recipe(
            request.description,
            request.servings,
            request.dietary_preference,
            request.max_new_tokens
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Could not generate the recipe: {error}"
        )

    if not recipe["ingredients"] and not recipe["steps"]:

        raise HTTPException(
            status_code=502,
            detail=(
                "The model did not return a usable recipe. Try a more specific "
                "description or a higher max_new_tokens. "
                f"Raw output: {raw_output[:500]}"
            )
        )

    # Only surface the raw text when part of the procedure is missing, so the
    # caller can see what the model actually said.
    incomplete = not recipe["ingredients"] or not recipe["steps"]

    return RecipeResponse(
        **recipe,
        device=DEVICE,
        raw_output=raw_output if incomplete else None
    )
