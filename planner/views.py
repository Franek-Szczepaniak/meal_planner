from django.shortcuts import render, redirect
from django.conf import settings
import json
import os
from .greedy import greedy_meal_planner_advanced
from .aco import aco_meal_planner
from .models import FamilyMember
from .calculator import calculate_family_needs
from .forms import FamilyMemberForm

# --- PRZELICZNIKI JEDNOSTEK NA GRAMY ---
TO_GRAMS = {
    'g': 1.0, 'kg': 1000.0, 'ml': 1.0, 'l': 1000.0,
    'cup': 240.0, 'tbsp': 15.0, 'tsp': 5.0, 'oz': 28.35,
    'lb': 453.59, 'pinch': 0.5, 'clove': 5.0, 'slice': 20.0,
    'package': 250.0, 'can': 400.0, 'jar': 300.0, 'pc': 150.0
}

def index(request):
    json_path = os.path.join(settings.BASE_DIR, 'algorithm_input_data.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        recipes = json.load(f)

    # Budowanie listy składników
    all_ingredients = set()
    ingredient_units = {}
    for r in recipes:
        for ing_name, ing_data in r['ingredients'].items():
            all_ingredients.add(ing_name)
            if isinstance(ing_data, dict):
                ingredient_units[ing_name] = ing_data.get('unit', 'pc')
            else:
                ingredient_units[ing_name] = 'pc'
    all_ingredients = sorted(list(all_ingredients))

    # --- OBSŁUGA BAZY PROFILI RODZINY ---
    family_profiles = FamilyMember.objects.all()
    family_list = [
        {
            'name': m.name, 'weight': m.weight, 'height': m.height,
            'age': m.age, 'gender': m.gender, 'activity': m.activity_level, 'goal': m.goal
        } for m in family_profiles
    ]
    
    family_goals = calculate_family_needs(family_list)

    target_kcal = family_goals['total_kcal']
    target_pro = family_goals['total_protein']
    target_fat = family_goals['total_fat']
    target_carb = family_goals['total_carbs']
    
    my_fridge = {}
    initial_fridge_raw = {}
    selected_algo = 'greedy'
    weight_waste = weight_kcal = weight_macro = 5
    
    # NOWE: Domyślne wartości dla dni i posiłków
    current_days = 4
    current_meals = 3 
    
    planned_schedule = []
    leftovers = {}

    member_form = FamilyMemberForm()

    if request.method == 'POST':
        if 'add_member' in request.POST:
            form = FamilyMemberForm(request.POST)
            if form.is_valid():
                form.save()
                return redirect('index')
                
        elif 'delete_member_id' in request.POST:
            member_id = request.POST.get('delete_member_id')
            FamilyMember.objects.filter(id=member_id).delete()
            return redirect('index')

        elif 'calculate_schedule' in request.POST:
            selected_algo = request.POST.get('algorithm', 'greedy')
            weight_waste = int(request.POST.get('weight_waste', 5))
            weight_kcal = int(request.POST.get('weight_kcal', 5))
            weight_macro = int(request.POST.get('weight_macro', 5))
            
            # NOWE: Odbieranie wartości z HTML
            current_days = int(request.POST.get('days', 4))
            current_meals = int(request.POST.get('meals_per_day', 3))
            
            ing_names = request.POST.getlist('ing_name[]')
            ing_qtys = request.POST.getlist('ing_qty[]')
            
            for name, qty in zip(ing_names, ing_qtys):
                if name and qty:
                    qty_float = float(qty)
                    initial_fridge_raw[name] = qty_float
                    unit = ingredient_units.get(name, 'pc')
                    my_fridge[name] = qty_float * TO_GRAMS.get(unit, 1.0)

            # Przekazywanie 'days' i 'meals_per_day' do algorytmów
            if selected_algo == 'aco':
                planned_schedule, leftovers = aco_meal_planner(
                    recipes, my_fridge, target_kcal, target_pro, target_fat, target_carb,
                    meals_per_day=current_meals, days=current_days, # <--- TUTAJ
                    weight_waste=weight_waste, weight_kcal=weight_kcal, weight_macro=weight_macro
                )
            else:
                planned_schedule, leftovers = greedy_meal_planner_advanced(
                    recipes, my_fridge, target_kcal, target_pro, target_fat, target_carb,
                    meals_per_day=current_meals, days=current_days, # <--- I TUTAJ
                    weight_waste=weight_waste, weight_kcal=weight_kcal, weight_macro=weight_macro
                )

    initial_fridge = [
        {'name': name, 'qty': qty, 'unit': ingredient_units.get(name, 'pc')}
        for name, qty in initial_fridge_raw.items()
    ]
    
    leftovers_formatted = []
    for name, qty_in_grams in leftovers.items():
        unit = ingredient_units.get(name, 'pc')
        original_qty = qty_in_grams / TO_GRAMS.get(unit, 1.0)
        leftovers_formatted.append({'name': name, 'qty': round(original_qty, 1), 'unit': unit})

    # obliczanie średnich wyników
    total_kcal = sum(meal['kcal'] for meal in planned_schedule)
    total_pro = sum(meal['protein'] for meal in planned_schedule)
    total_fat = sum(meal['fat'] for meal in planned_schedule)
    total_carb = sum(meal['carbs'] for meal in planned_schedule)
    
    # Dzielenie przez właściwą, dynamiczną liczbę posiłków dziennie
    days_planned = len(planned_schedule) / current_meals if planned_schedule and current_meals > 0 else 0
    
    avg_kcal = round(total_kcal / days_planned, 1) if days_planned > 0 else 0
    avg_pro = round(total_pro / days_planned, 1) if days_planned > 0 else 0
    avg_fat = round(total_fat / days_planned, 1) if days_planned > 0 else 0
    avg_carb = round(total_carb / days_planned, 1) if days_planned > 0 else 0

    context = {
        'schedule': planned_schedule,
        'initial_fridge': initial_fridge,
        'leftovers': leftovers_formatted,
        'avg_kcal': avg_kcal,
        'avg_pro': avg_pro,
        'avg_fat': avg_fat,
        'avg_carb': avg_carb,
        'target_kcal': target_kcal,
        'target_pro': target_pro,
        'target_fat': target_fat,
        'target_carb': target_carb,
        'all_ingredients': all_ingredients,
        'selected_algo': selected_algo,
        'weight_waste': weight_waste,
        'weight_kcal': weight_kcal,
        'weight_macro': weight_macro,
        'current_days': current_days,   # <--- NOWE
        'current_meals': current_meals, # <--- NOWE
        'ingredient_units': ingredient_units,
        'family_members': family_profiles, 
        'family_goals': family_goals,       
        'member_form': member_form,         
    }
    return render(request, 'planner/index.html', context)