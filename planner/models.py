from django.db import models

class FamilyMember(models.Model):
    GENDER_CHOICES = [
        ('M', 'Mężczyzna'),
        ('F', 'Kobieta'),
    ]
    GOAL_CHOICES = [
        ('lose', 'Odchudzanie (-500 kcal)'),
        ('maintain', 'Utrzymanie wagi'),
        ('gain', 'Budowa masy (+500 kcal)'),
    ]
    ACTIVITY_CHOICES = [
        (1.2, 'Siedzący (brak ćwiczeń)'),
        (1.375, 'Niska aktywność (ćwiczenia 1-3x w tyg)'),
        (1.55, 'Średnia aktywność (ćwiczenia 3-5x w tyg)'),
        (1.725, 'Wysoka aktywność (ćwiczenia codziennie)'),
        (1.9, 'Bardzo wysoka (praca fizyczna)'),
    ]
    
    name = models.CharField(max_length=50)
    weight = models.FloatField(help_text="Waga w kg")
    height = models.FloatField(help_text="Wzrost w cm")
    age = models.IntegerField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    activity_level = models.FloatField(choices=ACTIVITY_CHOICES) # <--- DODANE CHOICES
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES)

    def __str__(self):
        return self.name