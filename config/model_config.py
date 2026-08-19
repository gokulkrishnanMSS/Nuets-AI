from pathlib import Path

import torch
from transformers import (
    AutoProcessor,
    Qwen3VLForConditionalGeneration
)

BASE_DIR = Path(__file__).resolve().parent.parent

WEIGHTS_DIR = BASE_DIR / "weights"

MODEL_ID = "models--Qwen--Qwen3-VL-2B-Instruct"


def is_valid_model_dir(dir_path: Path) -> bool:
    """Check if directory contains both config and model weight files."""
    if not (dir_path / "config.json").is_file():
        return False
    return any(
        (dir_path / f).is_file()
        for f in (
            "model.safetensors",
            "pytorch_model.bin",
            "model.safetensors.index.json",
            "pytorch_model.bin.index.json",
        )
    )


def resolve_model_path() -> Path:
    """Locate the downloaded snapshot or model directory inside weights/."""

    direct_dir = WEIGHTS_DIR / "Qwen3-VL-2B-Instruct"
    if is_valid_model_dir(direct_dir):
        return direct_dir

    snapshots_dir = WEIGHTS_DIR / MODEL_ID / "snapshots"

    if snapshots_dir.is_dir():

        for snapshot in sorted(snapshots_dir.iterdir()):

            if is_valid_model_dir(snapshot):
                return snapshot

    print(f"Downloading model 'Qwen/Qwen3-VL-2B-Instruct' into '{direct_dir}'...")
    from huggingface_hub import snapshot_download

    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id="Qwen/Qwen3-VL-2B-Instruct",
        local_dir=direct_dir
    )
    return direct_dir


MODEL_PATH = resolve_model_path()

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

# float16/bfloat16 on GPU (CUDA/MPS) for memory & speed optimization
DTYPE = (
    torch.bfloat16
    if DEVICE == "mps"
    else torch.float16
    if DEVICE == "cuda"
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
