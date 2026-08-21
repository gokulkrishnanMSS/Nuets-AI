import io
import threading

import torch
from PIL import Image, UnidentifiedImageError

from config.model_config import (
    DEVICE,
    model,
    processor
)
from service.exceptions import FoodNotRecognisedError

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
    ) -> tuple[str, list[str], list[dict], float]:

        image = self.load_image(image_bytes)

        result = self.describe_image(
            image,
            prompt,
            max_new_tokens
        )

        # Calories are asked for first so a reply cut off by the token limit
        # still carries them.
        ingredients_prompt = (
            "Identify the food in this image, estimate its calories, and list "
            "its ingredients. Return ONLY a valid JSON object, for example: "
            '{"calories_kcal": 850, "ingredients": ["pizza dough", "tomato sauce"]}. '
            "calories_kcal must be a plain number, your best estimate of the "
            "total calories of the food shown. If the image shows no food or "
            'drink at all, return {"calories_kcal": 0, "ingredients": []}. '
            "Do not include markdown formatting, code fences, or any extra text."
        )

        raw_ingredients = self.describe_image(
            image,
            ingredients_prompt,
            max_new_tokens=160
        )

        calories_kcal = self.parse_calories(raw_ingredients)

        # The model puts no calories on something it does not read as food.
        if calories_kcal <= 0:

            raise FoodNotRecognisedError(
                "No food could be identified in the uploaded image."
            )

        ingredients = self.parse_ingredients(raw_ingredients)
        nutrition_info = self.fetch_nutrition(ingredients)

        return result, ingredients, nutrition_info, calories_kcal

    def parse_calories(self, text: str) -> float:
        """Read the model's calorie estimate out of its JSON reply.

        Returns 0.0 when the model gave no usable number, which the caller
        treats as "this is not food".
        """

        import json
        import re

        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        keys = (
            "calories_kcal",
            "calories",
            "total_calories_kcal",
            "total_calories",
            "kcal"
        )

        try:
            data = json.loads(cleaned)
        except Exception:
            data = None

        if isinstance(data, dict):

            for key in keys:

                if key in data:

                    calories = self.to_calories(data[key])

                    if calories > 0:
                        return calories

        # Truncated or chatty reply: pull the number next to the calorie key.
        match = re.search(
            r"(?:calories_kcal|total_calories|calories|kcal)\"?\s*[:=]\s*\"?\s*(\d+(?:\.\d+)?)",
            cleaned,
            flags=re.IGNORECASE
        )

        return float(match.group(1)) if match else 0.0

    def to_calories(self, value) -> float:
        """Accept 850, "850" or "850 kcal" and return a number."""

        import re

        if isinstance(value, bool):
            return 0.0

        if isinstance(value, (int, float)):
            return max(float(value), 0.0)

        if not isinstance(value, str):
            return 0.0

        match = re.search(r"\d+(?:\.\d+)?", value)

        return float(match.group()) if match else 0.0

    def fetch_nutrition(self, ingredients: list[str]) -> list[dict]:
        import psycopg2
        nutrition_data = []
        if not ingredients:
            return nutrition_data
            
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="macbook-pro",
                password="Mini@pass001",
                dbname="postgres"
            )
            cur = conn.cursor()
            
            for ingredient in ingredients:
                # Use ILIKE for case-insensitive partial match
                # e.g., if ingredient is "pizza dough", it will match "%pizza dough%"
                cur.execute(
                    "SELECT * FROM nutrition_data WHERE ingredient ILIKE %s LIMIT 1;",
                    (f"%{ingredient}%",)
                )
                row = cur.fetchone()
                if row:
                    cols = [desc[0] for desc in cur.description]
                    nutrient_dict = dict(zip(cols, row))
                    nutrient_dict['matched_ingredient'] = ingredient
                    nutrition_data.append(nutrient_dict)
                    
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching nutrition from DB: {e}")
            
        return nutrition_data

    def save_scan_result(self, result: str, ingredients: list[str], nutrition_info: list[dict]):
        import psycopg2
        import json
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="macbook-pro",
                password="Mini@pass001",
                dbname="postgres"
            )
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id SERIAL PRIMARY KEY,
                    result TEXT,
                    ingredients JSONB,
                    nutrition_info JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            cur.execute(
                """
                INSERT INTO scan_results (result, ingredients, nutrition_info)
                VALUES (%s, %s, %s)
                RETURNING id;
                """,
                (result, json.dumps(ingredients), json.dumps(nutrition_info))
            )
            scan_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            print(f"Successfully saved scan result with id: {scan_id}")
        except Exception as e:
            print(f"Error saving scan result to DB: {e}")

    def get_scan_results(self, limit: int = 10, offset: int = 0) -> list[dict]:
        import psycopg2
        results = []
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="macbook-pro",
                password="Mini@pass001",
                dbname="postgres"
            )
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id SERIAL PRIMARY KEY,
                    result TEXT,
                    ingredients JSONB,
                    nutrition_info JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            cur.execute(
                """
                SELECT id, result, ingredients, nutrition_info, created_at
                FROM scan_results
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
                """,
                (limit, offset)
            )
            rows = cur.fetchall()
            for row in rows:
                results.append({
                    "id": row[0],
                    "result": row[1],
                    "ingredients": row[2],
                    "nutrition_info": row[3],
                    "created_at": str(row[4])
                })
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error fetching scan results from DB: {e}")
        return results

    def search_scan_results(self, query: str, limit: int = 10, offset: int = 0) -> list[dict]:
        import psycopg2
        results = []
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="macbook-pro",
                password="Mini@pass001",
                dbname="postgres"
            )
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scan_results (
                    id SERIAL PRIMARY KEY,
                    result TEXT,
                    ingredients JSONB,
                    nutrition_info JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            search_query = f"%{query}%"
            cur.execute(
                """
                SELECT id, result, ingredients, nutrition_info, created_at
                FROM scan_results
                WHERE result ILIKE %s OR ingredients::text ILIKE %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s;
                """,
                (search_query, search_query, limit, offset)
            )
            rows = cur.fetchall()
            for row in rows:
                results.append({
                    "id": row[0],
                    "result": row[1],
                    "ingredients": row[2],
                    "nutrition_info": row[3],
                    "created_at": str(row[4])
                })
            cur.close()
            conn.close()
        except Exception as e:
            print(f"Error searching scan results from DB: {e}")
        return results

    def get_scan_result_by_id(self, scan_id: int) -> dict | None:
        import psycopg2
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5432",
                user="macbook-pro",
                password="Mini@pass001",
                dbname="postgres"
            )
            cur = conn.cursor()
            
            cur.execute(
                """
                SELECT id, result, ingredients, nutrition_info, created_at
                FROM scan_results
                WHERE id = %s;
                """,
                (scan_id,)
            )
            row = cur.fetchone()
            cur.close()
            conn.close()
            if row:
                return {
                    "id": row[0],
                    "result": row[1],
                    "ingredients": row[2],
                    "nutrition_info": row[3],
                    "created_at": str(row[4])
                }
        except Exception as e:
            print(f"Error fetching scan result from DB: {e}")
        return None

    def parse_ingredients(self, text: str) -> list[str]:
        import json
        import re

        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned).strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return [str(item).strip() for item in data if str(item).strip()]
            elif isinstance(data, dict) and "ingredients" in data and isinstance(data["ingredients"], list):
                return [str(item).strip() for item in data["ingredients"] if str(item).strip()]
        except Exception:
            pass

        lines = cleaned.splitlines()
        ingredients = []
        for line in lines:
            line = re.sub(r"^[\s\-\*\d\.\•]+", "", line).strip()
            if line:
                if "," in line and not (line.startswith("[") and line.endswith("]")):
                    parts = [p.strip().strip('"\'') for p in line.split(",") if p.strip()]
                    ingredients.extend(parts)
                else:
                    ingredients.append(line.strip('"\''))

        return ingredients

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
