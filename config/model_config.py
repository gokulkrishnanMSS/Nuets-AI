from pathlib import Path

import torch
from transformers import (
    AutoProcessor,
    Qwen3VLForConditionalGeneration
)

BASE_DIR = Path(__file__).resolve().parent.parent

WEIGHTS_DIR = BASE_DIR / "weights"

MODEL_ID = "models--Qwen--Qwen3-VL-2B-Instruct"


def resolve_model_path() -> Path:
    """Locate the downloaded snapshot inside weights/."""

    snapshots_dir = WEIGHTS_DIR / MODEL_ID / "snapshots"

    if snapshots_dir.is_dir():

        for snapshot in sorted(snapshots_dir.iterdir()):

            if (snapshot / "config.json").is_file():
                return snapshot

    raise FileNotFoundError(
        f"No snapshot with a config.json found for {MODEL_ID} under {WEIGHTS_DIR}"
    )


MODEL_PATH = resolve_model_path()

DEVICE = (
    "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

# bfloat16 on MPS: float16 has too little exponent range for this model and
# leaks garbage tokens into the output ("a popular American fast food item]+$300,000").
DTYPE = (
    torch.bfloat16
    if DEVICE == "mps"
    else torch.float32
)

print(f"[model_config] device={DEVICE} dtype={DTYPE} path={MODEL_PATH}")

processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    local_files_only=True,
    dtype=DTYPE
)

model.to(DEVICE)
model.eval()
