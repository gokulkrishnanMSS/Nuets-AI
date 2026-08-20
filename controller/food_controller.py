from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, BackgroundTasks
from PIL import UnidentifiedImageError

from config.model_config import DEVICE
from schemas.common import ErrorResponse
from schemas.food import FoodRequest, FoodResponse
from service.food_service import FoodService

router = APIRouter(
    prefix="/food",
    tags=["Food"]
)

food_service = FoodService()


@router.post(
    "/identify",
    response_model=FoodResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Identify food and extract ingredients from an uploaded image"
)
def identify_food(
    request: Annotated[
        FoodRequest,
        Form(media_type="multipart/form-data")
    ],
    background_tasks: BackgroundTasks
) -> FoodResponse:

    image_bytes = request.image.file.read()

    try:

        result, ingredients, nutrition_info = food_service.identify_food(
            image_bytes,
            request.prompt,
            request.max_new_tokens
        )

    except (UnidentifiedImageError, OSError) as error:

        raise HTTPException(
            status_code=400,
            detail=f"Could not read the uploaded image: {error}"
        )

    background_tasks.add_task(
        food_service.save_scan_result,
        result,
        ingredients,
        nutrition_info
    )

    return FoodResponse(
        result=result,
        ingredients=ingredients,
        nutrition_info=nutrition_info,
        filename=request.image.filename or "upload",
        device=DEVICE
    )

@router.get(
    "/scans",
    summary="Get recent scan results"
)
def get_scans(limit: int = 10, offset: int = 0):
    return food_service.get_scan_results(limit, offset)

@router.get(
    "/scans/search",
    summary="Search scan results by keyword"
)
def search_scans(query: str, limit: int = 10, offset: int = 0):
    return food_service.search_scan_results(query, limit, offset)

@router.get(
    "/scans/{scan_id}",
    responses={404: {"model": ErrorResponse}},
    summary="Get details of a specific scan result"
)
def get_scan_by_id(scan_id: int):
    result = food_service.get_scan_result_by_id(scan_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scan result not found")
    return result
