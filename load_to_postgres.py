import csv
import psycopg2

# Database connection parameters
DB_HOST = "localhost"
DB_PORT = "5432"
DB_USER = "macbook-pro"
DB_PASS = "Mini@pass001"
DB_NAME = "postgres"  # Using default postgres database, change if needed

CSV_FILE = r"/Users/gokul/ZiliconCloud/Python/Nuets/food_ingredients_nutrition_per_10g_generic.csv"

def load_data_to_postgres():
    print(f"Connecting to PostgreSQL at {DB_HOST}:{DB_PORT}...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            dbname=DB_NAME
        )
        cur = conn.cursor()
        
        # Create table if it doesn't exist
        print("Creating table 'nutrition_data' if it doesn't exist...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_data (
                id SERIAL PRIMARY KEY,
                ingredient TEXT UNIQUE,
                calories_kcal REAL,
                protein_g REAL,
                fat_g REAL,
                carbs_g REAL,
                fiber_g REAL,
                sugar_g REAL,
                calcium_mg REAL,
                iron_mg REAL,
                sodium_mg REAL,
                potassium_mg REAL,
                vitamin_c_mg REAL,
                cholesterol_mg REAL
            );
        """)
        
        # Optional: clear existing data before loading new data
        cur.execute("TRUNCATE TABLE nutrition_data RESTART IDENTITY;")
        
        print(f"Reading data from {CSV_FILE}...")
        count = 0
        with open(CSV_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader) # Skip header row
            
            for row in reader:
                if len(row) >= 13:
                    ingredient = row[0]
                    
                    # Convert to float, fallback to 0.0 if empty
                    def get_float(val):
                        try:
                            return float(val) if val else 0.0
                        except ValueError:
                            return 0.0
                            
                    vals = [get_float(x) for x in row[1:13]]
                    
                    cur.execute(
                        """
                        INSERT INTO nutrition_data (
                            ingredient, calories_kcal, protein_g, fat_g, carbs_g, fiber_g, sugar_g,
                            calcium_mg, iron_mg, sodium_mg, potassium_mg, vitamin_c_mg, cholesterol_mg
                        ) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                        ON CONFLICT (ingredient) DO UPDATE SET 
                            calories_kcal = EXCLUDED.calories_kcal,
                            protein_g = EXCLUDED.protein_g,
                            fat_g = EXCLUDED.fat_g,
                            carbs_g = EXCLUDED.carbs_g,
                            fiber_g = EXCLUDED.fiber_g,
                            sugar_g = EXCLUDED.sugar_g,
                            calcium_mg = EXCLUDED.calcium_mg,
                            iron_mg = EXCLUDED.iron_mg,
                            sodium_mg = EXCLUDED.sodium_mg,
                            potassium_mg = EXCLUDED.potassium_mg,
                            vitamin_c_mg = EXCLUDED.vitamin_c_mg,
                            cholesterol_mg = EXCLUDED.cholesterol_mg;
                        """,
                        [ingredient] + vals
                    )
                    count += 1
                    
        conn.commit()
        cur.close()
        conn.close()
        print(f"Successfully loaded {count} ingredients into the 'nutrition_data' table in PostgreSQL!")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    load_data_to_postgres()
