# planner/forms.py
from django import forms
from .models import FamilyMember

class FamilyMemberForm(forms.ModelForm):
    class Meta:
        model = FamilyMember
        fields = ['name', 'weight', 'height', 'age', 'gender', 'activity_level', 'goal']
        labels = {
            'name': 'Imię / Opis',
            'weight': 'Waga (kg)',
            'height': 'Wzrost (cm)',
            'age': 'Wiek (lata)',
            'gender': 'Płeć',
            'activity_level': 'Poziom aktywności',
            'goal': 'Cel diety',
        }