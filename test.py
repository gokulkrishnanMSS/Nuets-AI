from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, Qwen3VLForConditionalGeneration

MODEL_PATH = Path(
    "/Users/gokul/ZiliconCloud/Python/Nuets/weights/models--Qwen--Qwen3-VL-2B-Instruct/snapshots/89644892e4d85e24eaac8bacfd4f463576704203"
)

IMAGE_PATH = Path(
    "/Users/gokul/ZiliconCloud/Python/Nuets/Hamburger.jpeg"
)

DEVICE = "mps" if torch.backends.mps.is_available() else "cpu"

print(f"Using device: {DEVICE}")

processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    local_files_only=True
)

model = Qwen3VLForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    local_files_only=True,
    torch_dtype=torch.float16 if DEVICE == "mps" else torch.float32
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