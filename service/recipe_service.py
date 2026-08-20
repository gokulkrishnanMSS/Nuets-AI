import json
import re

import torch

from config.model_config import (
    DEVICE,
    model,
    processor
)
# The same lock the image endpoints use: one model instance, one generation at
# a time, so concurrent requests never share a device context.
from service.food_service import generate_lock

SYSTEM_PROMPT = (
    "You are a professional chef and a registered dietitian. "
    "You turn a description of a dish into a complete, healthy preparation procedure. "
    "Healthy means: minimal added oil (prefer olive or cold-pressed oils, measured in "
    "teaspoons), no deep frying (bake, steam, grill, saute, air-fry or pressure-cook "
    "instead), whole grains over refined flour, lean protein or legumes, plenty of "
    "vegetables, low added sugar and low sodium (build flavour with herbs, spices, "
    "citrus and aromatics). Keep the dish recognisable as what the user asked for. "
    "You reply with JSON only."
)

RECIPE_SCHEMA = """{
  "dish_name": "string",
  "summary": "one or two sentences about this healthy version",
  "prep_time_minutes": 0,
  "cook_time_minutes": 0,
  "total_time_minutes": 0,
  "ingredients": [
    {"item": "string", "quantity": "amount with unit", "notes": "healthier swap or prep note"}
  ],
  "steps": [
    {"step_number": 1, "instruction": "what to do", "duration_minutes": 0}
  ],
  "health_notes": ["what makes this preparation healthy"],
  "nutrition_estimate": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0}
}"""


class RecipeService:

    def generate_recipe(
        self,
        description: str,
        servings: int = 2,
        dietary_preference: str | None = None,
        max_new_tokens: int = 1536
    ) -> tuple[dict, str]:
        """Return the parsed recipe dict plus the raw model text."""

        prompt = self.build_prompt(
            description,
            servings,
            dietary_preference
        )

        raw_output = self.generate_text(
            prompt,
            max_new_tokens
        )

        recipe = self.parse_recipe(raw_output)

        return self.normalise_recipe(recipe, description, servings), raw_output

    def build_prompt(
        self,
        description: str,
        servings: int,
        dietary_preference: str | None
    ) -> str:

        dietary_line = (
            f"The recipe must respect this dietary requirement: {dietary_preference}.\n"
            if dietary_preference
            else ""
        )

        return (
            f"Dish description: {description}\n"
            f"Servings: {servings}\n"
            f"{dietary_line}"
            "\nWrite the healthy preparation procedure for this dish. "
            "Give each ingredient with a quantity scaled to the number of servings, "
            "realistic prep and cooking times in minutes, and clear numbered steps "
            "from start to serving.\n\n"
            "Budget your output so the whole JSON object is complete:\n"
            "- at most 12 ingredients, only the ones the dish really needs\n"
            "- keep every \"notes\" value under 6 words, or use an empty string\n"
            "- 6 to 10 steps, one short sentence each\n"
            "- at most 3 health_notes\n"
            "- always finish with nutrition_estimate and close the JSON\n\n"
            "Respond with ONLY a JSON object in exactly this shape "
            "(no markdown, no code fences, no commentary):\n"
            f"{RECIPE_SCHEMA}"
        )

    def generate_text(
        self,
        prompt: str,
        max_new_tokens: int = 1536
    ) -> str:

        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT
                    }
                ]
            },
            {
                "role": "user",
                "content": [
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
                    max_new_tokens=max_new_tokens,
                    do_sample=False
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

    def parse_recipe(self, text: str) -> dict:
        """Pull a recipe object out of the model text, repairing truncated JSON."""

        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        candidate = self.extract_json_object(cleaned)

        if candidate is None:
            return {}

        for attempt in (candidate, self.close_truncated_json(candidate)):

            if not attempt:
                continue

            try:
                data = json.loads(attempt)
            except Exception:
                continue

            if isinstance(data, dict):
                return data

        return {}

    def extract_json_object(self, text: str) -> str | None:
        """Return the first balanced {...} block, ignoring braces inside strings."""

        start = text.find("{")

        if start == -1:
            return None

        depth = 0
        in_string = False
        escaped = False

        for index in range(start, len(text)):

            char = text[index]

            if in_string:

                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False

                continue

            if char == '"':
                in_string = True
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1

                if depth == 0:
                    return text[start:index + 1]

        # Unbalanced: generation ran out of tokens mid-object.
        return text[start:]

    def close_truncated_json(self, text: str) -> str | None:
        """Best-effort repair of a JSON object cut off by the token limit."""

        depth = 0
        in_string = False
        escaped = False
        stack = []
        last_complete = None

        for index, char in enumerate(text):

            if in_string:

                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False

                continue

            if char == '"':
                in_string = True
            elif char in "{[":
                stack.append(char)
            elif char in "}]":
                if stack:
                    stack.pop()

            if not in_string and char in "}]" and len(stack) >= 1:
                # A complete element inside the outer object: safe truncation point.
                last_complete = index

            depth = len(stack)

        if depth == 0 and not in_string:
            return text

        if last_complete is None:
            return None

        head = text[:last_complete + 1]

        # Re-count what is still open after cutting at the last complete element.
        stack = []
        in_string = False
        escaped = False

        for char in head:

            if in_string:

                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False

                continue

            if char == '"':
                in_string = True
            elif char in "{[":
                stack.append(char)
            elif char in "}]":
                if stack:
                    stack.pop()

        closers = "".join(
            "}" if opener == "{" else "]"
            for opener in reversed(stack)
        )

        return head + closers

    def normalise_recipe(
        self,
        data: dict,
        description: str,
        servings: int
    ) -> dict:
        """Coerce whatever the model returned into the response schema."""

        ingredients = self.normalise_ingredients(
            data.get("ingredients")
        )

        steps = self.normalise_steps(
            data.get("steps")
        )

        prep_time = self.to_minutes(data.get("prep_time_minutes"))
        cook_time = self.to_minutes(data.get("cook_time_minutes"))
        total_time = self.to_minutes(data.get("total_time_minutes"))

        if not total_time:
            total_time = prep_time + cook_time

        return {
            "dish_name": str(
                data.get("dish_name") or description
            ).strip()[:200],
            "summary": str(data.get("summary") or "").strip(),
            "servings": servings,
            "prep_time_minutes": prep_time,
            "cook_time_minutes": cook_time,
            "total_time_minutes": total_time,
            "ingredients": ingredients,
            "steps": steps,
            "health_notes": self.normalise_notes(
                data.get("health_notes")
            ),
            "nutrition_estimate": (
                data.get("nutrition_estimate")
                if isinstance(data.get("nutrition_estimate"), dict)
                else {}
            )
        }

    def normalise_ingredients(self, raw) -> list[dict]:

        if not isinstance(raw, list):
            return []

        ingredients = []

        for entry in raw:

            if isinstance(entry, dict):

                item = str(
                    entry.get("item")
                    or entry.get("name")
                    or entry.get("ingredient")
                    or ""
                ).strip()

                if not item:
                    continue

                ingredients.append({
                    "item": item,
                    "quantity": str(
                        entry.get("quantity")
                        or entry.get("amount")
                        or ""
                    ).strip(),
                    "notes": str(entry.get("notes") or "").strip()
                })

            elif str(entry).strip():

                ingredients.append({
                    "item": str(entry).strip(),
                    "quantity": "",
                    "notes": ""
                })

        return ingredients

    def normalise_steps(self, raw) -> list[dict]:

        if not isinstance(raw, list):
            return []

        steps = []

        for index, entry in enumerate(raw, start=1):

            if isinstance(entry, dict):

                instruction = str(
                    entry.get("instruction")
                    or entry.get("step")
                    or entry.get("text")
                    or ""
                ).strip()

                if not instruction:
                    continue

                number = entry.get("step_number") or entry.get("number")
                duration = self.to_minutes(entry.get("duration_minutes"))

                steps.append({
                    "step_number": self.to_minutes(number) or len(steps) + 1,
                    "instruction": instruction,
                    "duration_minutes": duration or None
                })

            elif str(entry).strip():

                steps.append({
                    "step_number": len(steps) + 1,
                    "instruction": re.sub(
                        r"^\s*\d+[\.\)]\s*",
                        "",
                        str(entry).strip()
                    ),
                    "duration_minutes": None
                })

        return steps

    def normalise_notes(self, raw) -> list[str]:

        if isinstance(raw, list):
            return [
                str(note).strip()
                for note in raw
                if str(note).strip()
            ]

        if isinstance(raw, str) and raw.strip():
            return [raw.strip()]

        return []

    def to_minutes(self, value) -> int:
        """Accept 25, '25', '25 minutes' or '1 hour' and return whole minutes."""

        if isinstance(value, bool):
            return 0

        if isinstance(value, (int, float)):
            return max(int(value), 0)

        if not isinstance(value, str):
            return 0

        text = value.lower()

        hours = re.search(r"(\d+(?:\.\d+)?)\s*(?:h|hour|hr)", text)
        minutes = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|min)", text)

        if hours or minutes:

            total = 0.0

            if hours:
                total += float(hours.group(1)) * 60

            if minutes:
                total += float(minutes.group(1))

            return int(total)

        plain = re.search(r"\d+(?:\.\d+)?", text)

        return int(float(plain.group())) if plain else 0
