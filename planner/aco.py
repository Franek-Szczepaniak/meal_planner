import random

# Przeliczanie jednostek na gramy
TO_GRAMS = {
    'g': 1.0, 'kg': 1000.0, 'ml': 1.0, 'l': 1000.0,
    'cup': 240.0, 'tbsp': 15.0, 'tsp': 5.0, 'oz': 28.35,
    'lb': 453.59, 'pinch': 0.5, 'clove': 5.0, 'slice': 20.0,
    'package': 250.0, 'can': 400.0, 'jar': 300.0, 'pc': 150.0
}

def aco_meal_planner(recipes, initial_fridge, target_kcal_daily, target_pro_daily, target_fat_daily, target_carb_daily, meals_per_day=3, days=4, weight_waste=5, weight_kcal=5, weight_macro=5):
    # Parametry algorytmu mrówkowego
    NUM_ANTS = 10         
    MAX_ITER = 15         
    EVAPORATION_RATE = 0.2 
    ALPHA = 1.0           
    BETA = 2.0            
    
    # Przeliczenie celów dziennych na jeden posiłek
    t_kcal = target_kcal_daily / meals_per_day
    t_pro = target_pro_daily / meals_per_day
    t_fat = target_fat_daily / meals_per_day
    t_carb = target_carb_daily / meals_per_day
    
    # Dynamiczne stałe z funkcji celu 
    W_WASTE = weight_waste * 2.0
    W_KCAL = weight_kcal * 0.2
    W_MACRO = weight_macro * 2.0
    
    # Inicjalizacja feromonów
    pheromones = {r['id']: 1.0 for r in recipes}
    
    best_global_schedule = []
    best_global_score = float('inf')
    best_global_fridge = {}
    
    total_meals_to_plan = meals_per_day * days

    for iteration in range(MAX_ITER):
        ant_solutions = []
        
        for ant in range(NUM_ANTS):
            current_fridge = initial_fridge.copy()
            schedule = []
            used_recipes = set()
            ant_total_score = 0
            
            for step in range(total_meals_to_plan):
                choices = []
                
                for r in recipes:
                    if r['id'] in used_recipes:
                        continue
                        
                    waste_score = 0
                    for ing_name, ing_data in r['ingredients'].items():
                        # konwersja na gramy
                        unit = ing_data.get('unit', 'pc')
                        required_qty_grams = ing_data['qty'] * TO_GRAMS.get(unit, 1.0)
                        
                        # Sprawdzamy stan lodówki w gramach
                        available_qty_grams = current_fridge.get(ing_name, 0)
                        
                        if available_qty_grams > 0:
                            waste_score -= min(available_qty_grams, required_qty_grams) * 10.0
                        else:
                            waste_score += required_qty_grams * 0.1
                
                    kcal_penalty = abs(r['kcal'] - t_kcal)
                    pro_penalty = abs(r['macros']['protein'] - t_pro)
                    fat_penalty = abs(r['macros']['fat'] - t_fat)
                    carb_penalty = abs(r['macros']['carbs'] - t_carb)
                    macro_penalty = pro_penalty + fat_penalty + carb_penalty
                    
                    step_score = (W_WASTE * waste_score) + (W_KCAL * kcal_penalty) + (W_MACRO * macro_penalty)
                    
                    if step_score <= 0:
                        eta = 1000000.0 + abs(step_score)
                    else:
                        eta = 1000.0 / step_score
                    
                    # Prawdopodobieństwo wyboru
                    tau = pheromones[r['id']]
                    probability = (tau ** ALPHA) * (eta ** BETA)
                    
                    choices.append((r, probability, step_score))
            
                if not choices:
                    break # Zabezpieczenie przed brakiem przepisów
                    
                # Ruletkowa metoda wyboru przepisu na podstawie prawdopodobieństwa
                total_prob = sum(c[1] for c in choices)
                if total_prob <= 0:
                    chosen_tuple = random.choice(choices)
                else:
                    rand_val = random.uniform(0, total_prob)
                    cumulative = 0.0
                    for c in choices:
                        cumulative += c[1]
                        if cumulative >= rand_val:
                            chosen_tuple = c
                            break

                chosen_recipe, _, chosen_score = chosen_tuple
                
                # Dodanie do harmonogramu i aktualizacja 
                schedule.append(chosen_recipe)
                used_recipes.add(chosen_recipe['id'])
                ant_total_score += chosen_score
                
                for ing_name, ing_data in chosen_recipe['ingredients'].items():
                    unit = ing_data.get('unit', 'pc')
                    required_qty_grams = ing_data['qty'] * TO_GRAMS.get(unit, 1.0)
                    
                    if ing_name in current_fridge:
                        current_fridge[ing_name] -= required_qty_grams
                        if current_fridge[ing_name] <= 0:
                            del current_fridge[ing_name]
        
            # Zapisanie rozwiązania danej mrówki
            ant_solutions.append({
                'schedule': schedule,
                'score': ant_total_score,
                'fridge': current_fridge
            })
            
            # Aktualizacja najlepszego globalnego rozwiązania
            if ant_total_score < best_global_score and len(schedule) == total_meals_to_plan:
                best_global_score = ant_total_score
                best_global_schedule = schedule
                best_global_fridge = current_fridge
                
        # Aktualizacja feromonów 
        # 1. Parowanie (Evaporation)
        for r_id in pheromones:
            pheromones[r_id] *= (1.0 - EVAPORATION_RATE)
            
        # 2. Zostawianie feromonów przez mrówki
        for ant_sol in ant_solutions:
            # Zabezpieczenie przed ujemnymi feromonami
            score = ant_sol['score']
            if score <= 0:
                deposit = 1000.0 + abs(score) 
            else:
                deposit = 10000.0 / score     
                
            for r in ant_sol['schedule']:
                pheromones[r['id']] += deposit

    
    formatted_schedule = []
    day = 1
    meal_num = 1
    for r in best_global_schedule:
        
        # Naprawa linku 
        recipe_link = str(r.get('link', ''))
        if recipe_link == 'nan':
            recipe_link = ''
        elif recipe_link and not recipe_link.startswith(('http://', 'https://')):
            recipe_link = 'https://' + recipe_link

        formatted_schedule.append({
            'day': day,
            'meal': meal_num,
            'name': r['name'],
            'link': recipe_link,
            'kcal': r['kcal'],
            'protein': r['macros']['protein'],
            'fat': r['macros']['fat'],
            'carbs': r['macros']['carbs']
        })
        meal_num += 1
        if meal_num > meals_per_day:
            meal_num = 1
            day += 1

    return formatted_schedule, best_global_fridge