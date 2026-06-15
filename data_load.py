import pandas as pd
import glob
import os
import ast
import re
import json
import difflib
import html

pd.set_option('display.max_columns', None)      
pd.set_option('display.max_rows', 10)          
pd.set_option('display.width', 1000)            

data_dir = '.'

print("1. Ładowanie i łączenie baz odżywczych...")
nutrition_files = glob.glob(os.path.join(data_dir, 'FOOD-DATA-GROUP*.csv'))
nutrition_dfs = [pd.read_csv(file) for file in nutrition_files]
nutrition_df = pd.concat(nutrition_dfs, ignore_index=True)
nutrition_df.drop_duplicates(inplace=True)

SAMPLE_SIZE = 10000
print(f"2. Wczytywanie i losowanie próbki {SAMPLE_SIZE} przepisów...")
recipes_df = pd.read_csv(os.path.join(data_dir, 'recipes_data.csv')).sample(n=SAMPLE_SIZE, random_state=42)

print("3. Tworzenie słownika wartości odżywczych (lookup table)...")
nutrition_lookup = {}
for _, row in nutrition_df.iterrows():
    food_name = str(row['food']).strip().lower()
    nutrition_lookup[food_name] = {
        'kcal': row['Caloric Value'],
        'protein': row['Protein'],
        'fat': row['Fat'],
        'carbs': row['Carbohydrates'],
        'fiber': row['Dietary Fiber'],
        'sodium': row['Sodium'],
        'iron': row['Iron']
    }

# FUNKCJE POMOCNICZE I SŁOWNIKI JEDNOSTEK 

UNIT_MAPPING = {
    'c.': 'cup', 'c': 'cup', 'cup': 'cup', 'cups': 'cup',
    'tsp.': 'tsp', 'tsp': 'tsp', 'teaspoon': 'tsp', 'teaspoons': 'tsp', 't.': 'tsp',
    'tbsp.': 'tbsp', 'tbsp': 'tbsp', 'tablespoon': 'tbsp', 'tablespoons': 'tbsp', 'T.': 'tbsp',
    'oz.': 'oz', 'oz': 'oz', 'ounce': 'oz', 'ounces': 'oz',
    'g': 'g', 'g.': 'g', 'gram': 'g', 'grams': 'g',
    'kg': 'kg', 'kilogram': 'kg',
    'lb': 'lb', 'lbs': 'lb', 'pound': 'lb', 'pounds': 'lb',
    'ml': 'ml', 'l': 'l',
    'pinch': 'pinch', 'dash': 'pinch',
    'clove': 'clove', 'cloves': 'clove',
    'slice': 'slice', 'slices': 'slice',
    'package': 'package', 'pkg': 'package',
    'can': 'can', 'cans': 'can',
    'jar': 'jar'
}

TO_GRAMS = {
    'g': 1.0, 'kg': 1000.0, 'ml': 1.0, 'l': 1000.0,
    'cup': 240.0, 'tbsp': 15.0, 'tsp': 5.0, 'oz': 28.35,
    'lb': 453.59, 'pinch': 0.5, 'clove': 5.0, 'slice': 20.0,
    'package': 250.0, 'can': 400.0, 'jar': 300.0, 'pc': 150.0   
}

def parse_list_string(string_list):
    try:
        return ast.literal_eval(string_list)
    except (ValueError, SyntaxError):
        return []

def extract_quantity_and_unit(raw_ingredient_str):
    qty = 1.0
    s = html.unescape(raw_ingredient_str).lower()
    
    s = re.sub(r'\bfrac12\b', ' 0.5 ', s)
    s = re.sub(r'\bfrac14\b', ' 0.25 ', s)
    s = re.sub(r'\bfrac18\b', ' 0.125 ', s)
    s = re.sub(r'\bfrac34\b', ' 0.75 ', s)
    s = re.sub(r'\bfrac13\b', ' 0.33 ', s)
    s = re.sub(r'\bfrac23\b', ' 0.67 ', s)

    unicode_fractions = {
        '½': '0.5', '⅓': '0.33', '⅔': '0.67', '¼': '0.25', '¾': '0.75',
        '⅕': '0.2', '⅖': '0.4', '⅗': '0.6', '⅘': '0.8', '⅙': '0.17',
        '⅚': '0.83', '⅛': '0.125', '⅜': '0.375', '⅝': '0.625', '⅞': '0.875'
    }
    for char, val in unicode_fractions.items():
        s = s.replace(char, f" {val} ")
        
    fraction_match = re.search(r'(?:(\d+)\s+)?(\d+)\s*\/\s*(\d+)', s)
    if fraction_match:
        whole = float(fraction_match.group(1)) if fraction_match.group(1) else 0.0
        num = float(fraction_match.group(2))
        den = float(fraction_match.group(3))
        if den != 0:
            qty = whole + (num / den)
    else:
        number_match = re.search(r'(\d+\.?\d*)', s)
        if number_match:
            qty = float(number_match.group(1))
            
    found_unit = "pc"  
    words = re.findall(r'[a-zA-Z\.]+', s)
    for word in words:
        if word in UNIT_MAPPING:
            found_unit = UNIT_MAPPING[word]
            break 
            
    if found_unit in ['cup', 'tsp', 'tbsp']:
        if qty == 12.0: qty = 0.5
        elif qty == 14.0: qty = 0.25
        elif qty == 18.0: qty = 0.125
        elif qty == 38.0: qty = 0.375
        elif qty == 58.0: qty = 0.625
        elif qty == 13.0: qty = 0.33
        elif qty == 23.0: qty = 0.67
        elif qty == 34.0: qty = 0.75
            
    return round(qty, 2), found_unit


# Główna pętla transformacji
print("4. Transformacja przepisów i inteligentne łączenie z bazą odżywczą...")
processed_recipes = []

known_foods = list(nutrition_lookup.keys())

def find_best_match(ingredient_name, options):
    # 1. Dokładne dopasowanie (idealny scenariusz)
    if ingredient_name in options:
        return ingredient_name
        
    # 2. heurystyka wspólnych słów
    # Usuwamy kulinarne modyfikatory, które wprowadzają szum, a nie definiują produktu
    stop_words = {'chopped', 'diced', 'minced', 'sliced', 'cooked', 'raw', 'fresh', 'dry', 'dried', 'peeled', 'unpeeled', 'frozen', 'canned', 'crushed', 'packaged', 'mix', 'leaves'}
    
    # Wyciągamy słowa kluczowe (min. 3 litery, omijając stop words)
    ing_words = set(w for w in re.findall(r'\b[a-z]{3,}\b', ingredient_name) if w not in stop_words)
    
    best_opt = None
    best_score = 0
    
    for opt in options:
        opt_words = set(w for w in re.findall(r'\b[a-z]{3,}\b', opt))
        common = ing_words.intersection(opt_words)
        
        if common:
            score = len(common) - (len(opt_words) * 0.1)
            
            if score > best_score:
                best_score = score
                best_opt = opt
                
    if best_opt:
        return best_opt
        
    # 3. Jeśli nie ma punktów wspólnych, ostateczny fallback dla literówek
    matches = difflib.get_close_matches(ingredient_name, options, n=1, cutoff=0.6)
    if matches:
        return matches[0]
        
    return None

for index, row in recipes_df.iterrows():
    if index % 100 == 0:
        print(f"Przetwarzanie wiersza: {index}...")
        
    recipe_id = f"rec_{index}"
    title = row['title']
    
    raw_ingredients = parse_list_string(row['ingredients'])
    ner_ingredients = parse_list_string(row['NER'])
    
    total_kcal = total_protein = total_fat = total_carbs = total_fiber = total_sodium = 0
    mapped_ingredients = {}
    
    for raw_str in raw_ingredients:
        clean_raw_str = html.unescape(raw_str).lower()
        qty, unit = extract_quantity_and_unit(raw_str)
        
        matched_ner = None
        for ner in sorted(ner_ingredients, key=len, reverse=True):
            if re.search(rf'\b{re.escape(ner.lower())}\b', clean_raw_str):
                matched_ner = ner.lower()
                break
                
        if matched_ner:
            matched_food = find_best_match(matched_ner, known_foods)
            
            if matched_food and matched_food not in mapped_ingredients:
                mapped_ingredients[matched_food] = {"qty": qty, "unit": unit}
                
                db_item = nutrition_lookup[matched_food]
                weight_in_grams = qty * TO_GRAMS.get(unit, 1.0)
                multiplier = weight_in_grams / 100.0 
                
                total_kcal += db_item['kcal'] * multiplier
                total_protein += db_item['protein'] * multiplier
                total_fat += db_item['fat'] * multiplier
                total_carbs += db_item['carbs'] * multiplier
                total_fiber += db_item['fiber'] * multiplier
                total_sodium += db_item['sodium'] * multiplier

    if len(mapped_ingredients) >= 5 and 10000 >= total_kcal > 100:
        processed_recipes.append({
            "id": recipe_id,
            "name": title,
            "link": str(row.get('link', '')),
            "kcal": round(total_kcal, 2),
            "macros": {
                "protein": round(total_protein, 2),
                "fat": round(total_fat, 2),
                "carbs": round(total_carbs, 2),
            },
            "micros": {
                "fiber": round(total_fiber, 2),
                "sodium": round(total_sodium, 2)
            },
            "ingredients": mapped_ingredients
        })

print(f"Udało się zmapować i przetworzyć {len(processed_recipes)} z {SAMPLE_SIZE} wylosowanych przepisów.")

# zapis do pliku
output_file = 'algorithm_input_data.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(processed_recipes, f, ensure_ascii=False, indent=4)

print(f"\nGotowe! Plik wejściowy dla algorytmu zapisano jako: {output_file}")