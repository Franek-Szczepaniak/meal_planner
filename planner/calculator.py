# planner/calculator.py

def calculate_personal_needs(weight_kg, height_cm, age_years, gender, activity_level, goal):
    """
    Kalkulator zapotrzebowania kalorycznego i makroskładników.
    gender: 'M' (Mężczyzna) lub 'F' (Kobieta)
    activity_level: 
        1.2 - brak aktywności (praca siedząca)
        1.375 - niska aktywność (trening 1-3x w tygodniu)
        1.55 - średnia aktywność (trening 3-5x w tygodniu)
        1.725 - wysoka aktywność (trening codziennie)
        1.9 - bardzo wysoka aktywność (praca fizyczna + trening)
    goal: 
        'lose' (-500 kcal)
        'maintain' (0 kcal)
        'gain' (+500 kcal)
    """
    
    # 1. Obliczanie BMR (Basal Metabolic Rate) - Wzór Mifflin-St Jeor
    if gender == 'M':
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) + 5
    else:
        bmr = (10 * weight_kg) + (6.25 * height_cm) - (5 * age_years) - 161
        
    # 2. Obliczanie TDEE (Total Daily Energy Expenditure)
    tdee = bmr * activity_level
    
    # 3. Dostosowanie do celu
    if goal == 'lose':
        target_kcal = tdee - 500
    elif goal == 'gain':
        target_kcal = tdee + 500
    else:
        target_kcal = tdee
        
    # Zabezpieczenie przed niebezpiecznie niskimi kaloriami
    if gender == 'M' and target_kcal < 1500:
        target_kcal = 1500
    if gender == 'F' and target_kcal < 1200:
        target_kcal = 1200
        
    # 4. Obliczanie Makroskładników (Standardy zdrowego odżywiania)
    # Białko: 1.8g na kg masy ciała (dobre dla zdrowia i sytości)
    # Tłuszcz: 25% całkowitej puli kalorii (1g tłuszczu to 9 kcal)
    # Węglowodany: reszta kalorii (1g węgli to 4 kcal)
    
    target_pro = 1.8 * weight_kg
    target_fat = (target_kcal * 0.25) / 9.0
    
    kcal_from_pro_and_fat = (target_pro * 4) + (target_fat * 9)
    target_carb = (target_kcal - kcal_from_pro_and_fat) / 4.0
    
    return {
        'kcal': round(target_kcal, 1),
        'protein': round(target_pro, 1),
        'fat': round(target_fat, 1),
        'carbs': round(target_carb, 1)
    }

def calculate_family_needs(family_members):
    """
    Sumuje zapotrzebowanie całej rodziny i wylicza procentowe udziały.
    """
    total_kcal = 0
    total_pro = 0
    total_fat = 0
    total_carb = 0
    
    results = []
    
    for member in family_members:
        needs = calculate_personal_needs(
            weight_kg=member['weight'],
            height_cm=member['height'],
            age_years=member['age'],
            gender=member['gender'],
            activity_level=member['activity'],
            goal=member['goal']
        )
        total_kcal += needs['kcal']
        total_pro += needs['protein']
        total_fat += needs['fat']
        total_carb += needs['carbs']
        
        results.append({
            'name': member['name'],
            'needs': needs
        })
        
    # Wyliczanie procentowego udziału każdego w posiłku (tzw. "wielkość porcji")
    for r in results:
        r['portion_percentage'] = round((r['needs']['kcal'] / total_kcal) * 100, 1) if total_kcal > 0 else 0
        
    return {
        'total_kcal': round(total_kcal, 1),
        'total_protein': round(total_pro, 1),
        'total_fat': round(total_fat, 1),
        'total_carbs': round(total_carb, 1),
        'members': results
    }