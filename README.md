# Wielokryterialny Optymalizator Jadłospisu Rodzinnego

Aplikacja webowa zbudowana w frameworku **Django**, rozwiązująca problem optymalizacji harmonogramu żywienia rodziny. Projekt wykorzystuje algorytmy optymalizacji do wielokryterialnego doboru posiłków na podstawie zapotrzebowania kalorycznego, makroskładników oraz zawartości lodówki użytkownika w duchu *Zero Waste*.

---

##  Główne funkcjonalności

* **Zarządzanie profilami rodziny:** Automatyczne wyliczanie wskaźników BMR (wzór Mifflin-St Jeor) oraz TDEE dla każdego domownika na podstawie wieku, płci, wagi, wzrostu, poziomu aktywności i obranego celu (odchudzanie, utrzymanie, masa).
* **Wirtualna Lodówka (Zero Waste):** Użytkownik wprowadza posiadane składniki w dowolnych jednostkach (sztuki, uncje, szklanki, łyżki). Aplikacja w locie standaryzuje je do gramów i priorytetyzuje przepisy, które pozwolą wyczyścić zapasy bez marnowania żywności.
* **Wyliczanie wielkości porcji:** System po ułożeniu idealnego "wspólnego garnka" generuje procentowy podział wielkości porcji dla każdego członka rodziny.
* **Wielokryterialna Funkcja Kosztu:** Optymalizacja uwzględnia wagi (suwaki od 1 do 10) definiowane przez użytkownika dla 3 celów: 
    * Minimalizacja marnowania jedzenia (Zgodność z lodówką).
    * Minimalizacja błędu kalorycznego (Kcal).
    * Minimalizacja błędu makroskładników (Białko, Tłuszcz, Węglowodany).

---

## Zaimplementowane Algorytmy 

Problem doboru kilkunastu przepisów z ogromnej bazy danych do złożonych wymagań żywieniowych jest problemem kombinatorycznym. Aby go rozwiązać, zaimplementowano dwa podejścia algorytmiczne:

### 1. Algorytm Mrówkowy (ACO - Ant Colony Optimization)
Metaheurystyka inspirowana zachowaniem roju mrówek szukających pożywienia. Algorytm iteracyjnie buduje rozwiązania, unikając wpadnięcia w minimum lokalne.
* **Heurystyka ($\eta$):** Ocenia "atrakcyjność" przepisu tu i teraz (kara za błędy makro/kcal oraz nagroda za czyszczenie lodówki).
* **Feromony ($\tau$):** "Pamięć stada". Mrówki, które ułożą najlepszy wielodniowy jadłospis, zostawiają wirtualny ślad feromonowy na użytych przepisach, zwiększając prawdopodobieństwo ich wyboru w kolejnych generacjach.
* **Zaleta:** Potrafi zaplanować strategię długoterminową (np. zjeść gorzej zbilansowane śniadanie, aby zaoszczędzić kluczowe składniki w lodówce na idealną kolację).

### 2. Algorytm Zachłanny (Greedy Algorithm)
Klasyczna metoda heurystyczna, która na każdym etapie budowania harmonogramu (krok po kroku) wybiera lokalnie optymalne rozwiązanie. 
* **Zaleta:** Ekstremalnie szybki czas wykonania. Oblicza funkcję kary dla każdego przepisu i bezlitośnie wybiera ten z najmniejszym odchyleniem w danej sekundzie. 
* **Wada:** Brak planowania długoterminowego (krótkowzroczność).

---

## 🛠️ Architektura i Technologie

* **Język:** Python 3.x
* **Framework backendowy:** Django (Architektura MVT - Model, View, Template)
* **Baza danych:** SQLite (wbudowana, do przetrzymywania modeli profili użytkowników)
* **Frontend:** HTML5, CSS3, JavaScript (dynamiczna obsługa wirtualnej lodówki)
* **Baza danych przepisów:** Plik JSON (`algorithm_input_data.json`) zawierający przetworzone przepisy z makroskładnikami i przelicznikami jednostek.

### Struktura najważniejszych plików
* `planner/models.py` - Definicja struktury w bazie danych (profil członka rodziny).
* `planner/calculator.py` - Moduł dietetyczny liczący TDEE i procentowy podział porcji.
* `planner/aco.py` - Implementacja sztucznej inteligencji roju (Algorytm Mrówkowy).
* `planner/greedy.py` - Implementacja algorytmu zachłannego.
* `planner/views.py` - Kontroler aplikacji, spinający interfejs webowy z silnikami optymalizacyjnymi oraz parserem jednostek (`TO_GRAMS`).

---

## ⚙️ Instalacja i Uruchomienie

Aby uruchomić projekt na lokalnym komputerze, wykonaj poniższe kroki w terminalu:

**1. Klonowanie repozytorium (lub wejście do folderu)**
```bash
cd nazwa-twojego-folderu
```

**2. Instalacja wymaganych bibliotek**
```bash
pip install django
```
**3.Migracja bazy danych (Inicjalizacja SQLite)**
```bash
python manage.py makemigrations
python manage.py migrate
```
**4.Uruchomienie serwera deweloperskiego**
```bash
python manage.py runserver
```
Po wykonaniu tych komend, aplikacja będzie dostępna w przeglądarce pod adresem: http://127.0.0.1:8000/.
