import json
import random


TO_GRAMS = {
    'g': 1.0, 'kg': 1000.0, 'ml': 1.0, 'l': 1000.0,
    'cup': 240.0, 'tbsp': 15.0, 'tsp': 5.0, 'oz': 28.35,
    'lb': 453.59, 'pinch': 0.5, 'clove': 5.0, 'slice': 20.0,
    'package': 250.0, 'can': 400.0, 'jar': 300.0, 'pc': 150.0
}

# Greedy optimization

def greedy_meal_planner_advanced(recipes, initial_fridge, target_kcal_daily, target_pro_daily, target_fat_daily, target_carb_daily, meals_per_day=3, days=4, weight_waste=5, weight_kcal=5, weight_macro=5):
    schedule = []
    current_fridge = initial_fridge.copy()
    used_recipes = set()
    
    # Przeliczenie celów dziennych na jeden posiłek
    t_kcal = target_kcal_daily / meals_per_day
    t_pro = target_pro_daily / meals_per_day
    t_fat = target_fat_daily / meals_per_day
    t_carb = target_carb_daily / meals_per_day
    
    
    W_WASTE = weight_waste * 2.0 
    W_KCAL = weight_kcal * 0.2      
    W_MACRO = weight_macro * 2.0
    

    for d in range(1, days + 1):
        for m in range(1, meals_per_day + 1):
            
            best_recipe = None
            best_score = float('inf')
            
            for r in recipes:
                if r['id'] in used_recipes:
                    continue
                    
                waste_score = 0
                for ing_name, ing_data in r['ingredients'].items():
                    unit = ing_data.get('unit', 'pc')
                    required_qty_grams = ing_data['qty'] * TO_GRAMS.get(unit, 1.0)
                    
                    # Sprawdzamy stan lodówki
                    available_qty_grams = current_fridge.get(ing_name, 0)
                    
                    if available_qty_grams > 0:
                        waste_score -= min(available_qty_grams, required_qty_grams) * 10.0
                    else:
                        waste_score += required_qty_grams * 0.1 
                
                # Penalty calculation
                kcal_penalty = abs(r['kcal'] - t_kcal)
                pro_penalty = abs(r['macros']['protein'] - t_pro)
                fat_penalty = abs(r['macros']['fat'] - t_fat)
                carb_penalty = abs(r['macros']['carbs'] - t_carb)
                macro_penalty = pro_penalty + fat_penalty + carb_penalty
                
                # Score function
                step_score = (W_WASTE * waste_score) + (W_KCAL * kcal_penalty) + (W_MACRO * macro_penalty)
                
                if step_score < best_score:
                    best_score = step_score
                    best_recipe = r
            
            if not best_recipe:
                break
                
            recipe_link = str(best_recipe.get('link', ''))
            if recipe_link == 'nan':
                recipe_link = ''
            elif recipe_link and not recipe_link.startswith(('http://', 'https://')):
                recipe_link = 'https://' + recipe_link

            schedule.append({
                'day': d,
                'meal': m,
                'name': best_recipe['name'],
                'link': recipe_link,
                'kcal': best_recipe['kcal'],
                'protein': best_recipe['macros']['protein'],
                'fat': best_recipe['macros']['fat'],
                'carbs': best_recipe['macros']['carbs']
            })
            used_recipes.add(best_recipe['id'])
            
            for ing_name, ing_data in best_recipe['ingredients'].items():
                unit = ing_data.get('unit', 'pc')
                required_qty_grams = ing_data['qty'] * TO_GRAMS.get(unit, 1.0)
                
                if ing_name in current_fridge:
                    current_fridge[ing_name] -= required_qty_grams
                    if current_fridge[ing_name] <= 0:
                        del current_fridge[ing_name]
                        
    return schedule, current_fridge