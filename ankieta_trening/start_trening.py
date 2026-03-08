import json
import os
import random
import sys

def run_training_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ankieta_path = os.path.join(base_dir, 'ankieta_j.json')
    baza_path = os.path.join(base_dir, '..', 'src', 'baza_cwiczen_j.json')
    output_path = os.path.join(base_dir, 'gotowy_plan_treningowy.json')

    try:
        with open(ankieta_path, 'r', encoding='utf-8') as f:
            ankieta = json.load(f)
        with open(baza_path, 'r', encoding='utf-8') as f:
            baza_cwiczen = json.load(f)
    except Exception as e:
        print(f"   [!] Błąd: {e}")
        return

    def get_val(key):
        if isinstance(ankieta, dict): return ankieta.get(key)
        return None

    # Pobranie liczby dni (domyślnie 3 jeśli brak danych)
    try:
        dni = int(get_val("dni") or 3)
    except:
        dni = 3

    # --- LOGIKA TEMPA ---
    def get_smart_tempo(cw_name):
        n = cw_name.lower()
        if any(x in n for x in ["martwy ciąg", "przysiad", "wyciskanie"]): return "3-1-1-0"
        if any(x in n for x in ["wyprosty", "uginanie", "rozpiętki", "brama", "wznosy"]): return "2-0-1-2"
        if any(x in n for x in ["wiosłowanie", "ściąganie"]): return "3-0-1-1"
        return "3-0-1-0"

    # --- FILTROWANIE BAZY ---
    used_exercises = set()

    def pick_exercise(muscle=None, type_f=None, gear_f=None, specific=None):
        opts = [cw for cw in baza_cwiczen if cw['Nazwa_Cwiczenia'] not in used_exercises]
        if muscle: opts = [cw for cw in opts if muscle.lower() in cw['Partia_Glowna'].lower()]
        if type_f: opts = [cw for cw in opts if cw['Typ ćwiczenia'] == type_f]
        if gear_f: opts = [cw for cw in opts if cw['Sprzet'] in gear_f]
        if specific: opts = [cw for cw in opts if specific.lower() in cw['Nazwa_Cwiczenia'].lower()]
        
        if not opts:
            opts = [cw for cw in baza_cwiczen if muscle and muscle.lower() in cw['Partia_Glowna'].lower()]
            if not opts: opts = baza_cwiczen
            
        chosen = random.choice(opts)
        used_exercises.add(chosen['Nazwa_Cwiczenia'])
        return chosen

    plan = []
    
    # --- SCENARIUSZ 4 DNI (PUSH/PULL) ---
    if dni >= 4:
        p1 = [pick_exercise(muscle="Czworogłowy", gear_f=["Maszyna"]), pick_exercise(muscle="Klatka", gear_f=["Maszyna"]), pick_exercise(muscle="Naramienny (bok)", gear_f=["Wyciąg"]), pick_exercise(muscle="Czworogłowy", type_f="Izolowane"), pick_exercise(muscle="Klatka", type_f="Izolowane"), pick_exercise(muscle="Triceps", gear_f=["Wyciąg"])]
        l1 = [pick_exercise(muscle="Najszerszy", specific="ściąganie"), pick_exercise(muscle="Dwugłowy", type_f="Wielostawowe"), pick_exercise(muscle="Najszerszy", specific="wiosłowanie"), pick_exercise(muscle="Naramienny (tył)"), pick_exercise(muscle="Dwugłowy", gear_f=["Maszyna"]), pick_exercise(muscle="Biceps", gear_f=["Hantle"])]
        p2 = [pick_exercise(muscle="Czworogłowy", gear_f=["Maszyna", "Sztanga"]), pick_exercise(muscle="Klatka", gear_f=["Hantle"]), pick_exercise(muscle="Naramienny", gear_f=["Sztanga", "Hantle"]), pick_exercise(muscle="Czworogłowy", specific="bułgarskie"), pick_exercise(muscle="Klatka", gear_f=["Wyciąg"]), pick_exercise(muscle="Triceps", gear_f=["Hantle"])]
        l2 = [pick_exercise(muscle="Najszerszy", gear_f=["Drążek"]), pick_exercise(muscle="Dwugłowy", specific="Dzień dobry"), pick_exercise(muscle="Najszerszy", gear_f=["Hantle"]), pick_exercise(muscle="Naramienny (tył)"), pick_exercise(muscle="Biceps", gear_f=["Sztanga"]), pick_exercise(muscle="brzucha")]
        session_data = [("PUSH 1", p1), ("PULL 1", l1), ("PUSH 2", p2), ("PULL 2", l2)]

    # --- SCENARIUSZ 3 DNI (PUSH / PULL / LEGS) ---
    else:
        push = [
            pick_exercise(muscle="Klatka", type_f="Wielostawowe"), # Klata złożone
            pick_exercise(muscle="Naramienny", type_f="Wielostawowe"), # Barki złożone
            pick_exercise(muscle="Klatka", type_f="Izolowane"), # Klata izolacja
            pick_exercise(muscle="Naramienny (bok)", type_f="Izolowane"), # Barki bok
            pick_exercise(muscle="Triceps", gear_f=["Wyciąg"]), # Triceps wyciąg
            pick_exercise(muscle="Triceps", gear_f=["Hantle"]) # Triceps hantle
        ]
        pull = [
            pick_exercise(muscle="Najszerszy", specific="ściąganie"), # Szerokość
            pick_exercise(muscle="Najszerszy", specific="wiosłowanie"), # Grubość
            pick_exercise(muscle="Naramienny", muscle="tył"), # Tył barku
            pick_exercise(muscle="Biceps", gear_f=["Sztanga"]), # Biceps masa
            pick_exercise(muscle="Biceps", gear_f=["Hantle"]), # Biceps kształt
            pick_exercise(muscle="brzucha") # Brzuch
        ]
        legs = [
            pick_exercise(muscle="Czworogłowy", type_f="Wielostawowe"), # Nogi przód
            pick_exercise(muscle="Dwugłowy", type_f="Wielostawowe"), # Nogi tył (RDL)
            pick_exercise(muscle="Czworogłowy", type_f="Izolowane"), # Wyprosty
            pick_exercise(muscle="Dwugłowy", type_f="Izolowane"), # Uginanie
            pick_exercise(muscle="łydki"), # Łydki
            pick_exercise(muscle="brzucha") # Brzuch
        ]
        session_data = [("PUSH (Góra przód)", push), ("PULL (Góra tył)", pull), ("LEGS (Nogi i brzuch)", legs)]

    for name, content in session_data:
        sesja = {"nazwa_sesji": name, "cwiczenia": []}
        for idx, cw in enumerate(content):
            s = 3 if idx < 4 else 2
            sesja["cwiczenia"].append({
                "nazwa": cw['Nazwa_Cwiczenia'],
                "serie": s,
                "powtorzenia": "8-10" if cw['Typ ćwiczenia'] == "Wielostawowe" else "10-12",
                "notatki": f"Tempo: {get_smart_tempo(cw['Nazwa_Cwiczenia'])}. {cw['Krótki opis techniki']}"
            })
        plan.append(sesja)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"✅ Skrypt dostosowany do {dni} dni treningowych.")

if __name__ == "__main__":
    run_training_pipeline()
