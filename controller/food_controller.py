from typing import Annotated

from fastapi import APIRouter, Form, HTTPException
from PIL import UnidentifiedImageError

from config.model_config import DEVICE
from dto.food_request import FoodRequest
from dto.food_response import FoodResponse
from service.food_service import FoodService

router = APIRouter(
    prefix="/food",
    tags=["Food"]
)

food_service = FoodService()


@router.post(
    "/identify",
    response_model=FoodResponse,
    summary="Identify food from an uploaded image"
)
def identify_food(
    request: Annotated[
        FoodRequest,
        Form(media_type="multipart/form-data")
    ]
) -> FoodResponse:

    image_bytes = request.image.file.read()

    try:

        result = food_service.identify_food(
            image_bytes,
            request.prompt,
            request.max_new_tokens
        )

    except (UnidentifiedImageError, OSError) as error:

        raise HTTPException(
            status_code=400,
            detail=f"Could not read the uploaded image: {error}"
        )

    return FoodResponse(
        result=result,
        filename=request.image.filename or "upload",
        device=DEVICE
    )
