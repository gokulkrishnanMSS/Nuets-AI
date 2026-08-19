import csv
import collections

base_path = r"C:\Users\gokul\Downloads\FoodData_Central_foundation_food_csv_2026-04-30\FoodData_Central_foundation_food_csv_2026-04-30"

print("Loading data...")

# 1. Load foundation foods: fdc_id -> description
foundation_foods = {}
with open(f"{base_path}\\food.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    # columns: fdc_id, data_type, description...
    for row in reader:
        fdc_id, data_type, description = row[0], row[1], row[2]
        if data_type == 'foundation_food':
            foundation_foods[fdc_id] = description

print(f"Found {len(foundation_foods)} foundation foods.")

# 2. Load nutrients: id -> (name, unit)
nutrients = {}
with open(f"{base_path}\\nutrient.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    # columns: id, name, unit_name...
    for row in reader:
        n_id, name, unit = row[0], row[1], row[2]
        nutrients[n_id] = (name, unit.lower())

print(f"Found {len(nutrients)} nutrients.")

# 3. Load food_nutrients and map
# Structure: food_desc -> list of "nutrient_name - amount unit"
# and also food_desc -> dict of "nutrient_name (unit)": amount
food_nutrient_list = collections.defaultdict(list)
food_nutrient_matrix = collections.defaultdict(dict)
all_nutrient_cols = set()

with open(f"{base_path}\\food_nutrient.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    # columns: id, fdc_id, nutrient_id, amount...
    for row in reader:
        fdc_id, n_id, amount = row[1], row[2], row[3]
        if fdc_id in foundation_foods and n_id in nutrients:
            desc = foundation_foods[fdc_id]
            n_name, n_unit = nutrients[n_id]
            
            # String representation
            n_string = f"{n_name} - {amount}{n_unit}"
            if n_string not in food_nutrient_list[desc]:
                food_nutrient_list[desc].append(n_string)
                
            # Matrix representation
            col_name = f"{n_name} ({n_unit})"
            food_nutrient_matrix[desc][col_name] = amount
            all_nutrient_cols.add(col_name)

print("Writing list format...")
# Write the list format CSV
list_out_path = f"{base_path}\\food_nutrients_list.csv"
with open(list_out_path, "w", encoding="utf-8", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(["Ingredient", "Nutrients"])
    for desc, nuts in food_nutrient_list.items():
        writer.writerow([desc, ", ".join(nuts)])

print("Writing matrix format...")
# Write the matrix format CSV
matrix_out_path = f"{base_path}\\food_nutrients_matrix.csv"
sorted_cols = sorted(list(all_nutrient_cols))

with open(matrix_out_path, "w", encoding="utf-8", newline='') as f:
    writer = csv.writer(f)
    header = ["Ingredient"] + sorted_cols
    writer.writerow(header)
    
    for desc, n_dict in food_nutrient_matrix.items():
        row = [desc]
        for col in sorted_cols:
            row.append(n_dict.get(col, ""))
        writer.writerow(row)

print("Successfully generated CSVs!")
print(f"1. {list_out_path}")
print(f"2. {matrix_out_path}")
