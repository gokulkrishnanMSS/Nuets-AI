import io
import threading

import torch
from PIL import Image, UnidentifiedImageError

from config.model_config import (
    DEVICE,
    model,
    processor
)

# One model instance shared by every request. FastAPI runs sync endpoints in a
# threadpool, so generation is serialised to keep concurrent calls off the same
# MPS context at the same time.
generate_lock = threading.Lock()


class FoodService:

    def identify_food(
        self,
        image_bytes: bytes,
        prompt: str,
        max_new_tokens: int = 64
    ) -> str:

        image = self.load_image(image_bytes)

        return self.describe_image(
            image,
            prompt,
            max_new_tokens
        )

    def load_image(
        self,
        image_bytes: bytes
    ) -> Image.Image:

        if not image_bytes:

            raise UnidentifiedImageError(
                "The uploaded file is empty."
            )

        with Image.open(
            io.BytesIO(image_bytes)
        ) as opened:

            return opened.convert("RGB")

    def describe_image(
        self,
        image: Image.Image,
        prompt: str,
        max_new_tokens: int = 64
    ) -> str:

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
                        "text": prompt
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

        inputs = inputs.to(DEVICE)

        with generate_lock:

            with torch.inference_mode():

                generated_ids = model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens
                )

        generated_ids_trimmed = [

            output_ids[len(input_id):]

            for input_id, output_ids in zip(
                input_ids,
                generated_ids
            )
        ]

        output = processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True
        )

        return output[0].strip()
