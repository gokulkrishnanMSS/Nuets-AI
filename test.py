from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
from huggingface_hub import snapshot_download

BASE_DIR = Path(__file__).resolve().parent
WEIGHTS_DIR = BASE_DIR / "weights"
IMAGE_PATH = BASE_DIR / "Hamburger.jpeg"

REPO_ID = "Qwen/Qwen3-VL-2B-Instruct"
LOCAL_MODEL_PATH = WEIGHTS_DIR / "Qwen3-VL-2B-Instruct"


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


def get_or_download_model_path() -> Path:
    """Locate model in project root weights/, downloading if not present."""
    if is_valid_model_dir(LOCAL_MODEL_PATH):
        print(f"Using local model at: {LOCAL_MODEL_PATH}", flush=True)
        return LOCAL_MODEL_PATH

    snapshots_dir = WEIGHTS_DIR / "models--Qwen--Qwen3-VL-2B-Instruct" / "snapshots"
    if snapshots_dir.is_dir():
        for snapshot in sorted(snapshots_dir.iterdir()):
            if is_valid_model_dir(snapshot):
                print(f"Using snapshot model at: {snapshot}", flush=True)
                return snapshot

    print(f"Downloading/completing model '{REPO_ID}' into '{LOCAL_MODEL_PATH}'...", flush=True)
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=REPO_ID,
        local_dir=LOCAL_MODEL_PATH
    )
    print(f"Model downloaded and saved to project root: {LOCAL_MODEL_PATH}", flush=True)
    return LOCAL_MODEL_PATH


MODEL_PATH = get_or_download_model_path()

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "mps"
    if torch.backends.mps.is_available()
    else "cpu"
)

print(f"Using device: {DEVICE}", flush=True)

processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    local_files_only=True,
    torch_dtype=torch.bfloat16 if DEVICE == "mps" else torch.float16 if DEVICE == "cuda" else torch.float32
)

model.to(DEVICE)
model.eval()

image = Image.open(IMAGE_PATH).convert("RGB")

messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image",
                "image": image
            },
            {
                "type": "text",
                "text": "Identify this food and describe it."
            }
        ]
    }
]

inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt"
)

input_ids = inputs["input_ids"]

inputs = {
    key: value.to(DEVICE)
    for key, value in inputs.items()
}

with torch.inference_mode():
    generated_ids = model.generate(
        **inputs,
        max_new_tokens=64
    )

generated_ids_trimmed = [
    output_ids[len(input_id):]
    for input_id, output_ids in zip(
        input_ids,
        generated_ids
    )
]

output_text = processor.batch_decode(
    generated_ids_trimmed,
    skip_special_tokens=True
)

print(output_text[0])