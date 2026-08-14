import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Lets `python app.py` and `uvicorn app:app` resolve the `config` / `dto` /
# `service` / `controller` imports regardless of the current working directory.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi import FastAPI  # noqa: E402
from fastapi.responses import RedirectResponse  # noqa: E402

from config.model_config import DEVICE, MODEL_PATH  # noqa: E402
from controller.food_controller import router  # noqa: E402

app = FastAPI(
    title="Nuets Food AI Service",
    description=(
        "Food identification powered by Qwen3-VL-2B-Instruct running locally.\n\n"
        "- **Swagger UI**: [/docs](/docs)\n"
        "- **ReDoc**: [/redoc](/redoc)\n"
        "- **OpenAPI schema**: [/openapi.json](/openapi.json)"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {
            "name": "Food",
            "description": "Identify and describe food in an image."
        },
        {
            "name": "Health",
            "description": "Service and model status."
        }
    ]
)

app.include_router(router)


@app.get(
    "/",
    include_in_schema=False
)
def root():

    return RedirectResponse(url="/docs")


@app.get(
    "/health",
    tags=["Health"],
    summary="Service and model status"
)
def health():

    return {
        "status": "ok",
        "device": DEVICE,
        "model_path": str(MODEL_PATH)
    }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
