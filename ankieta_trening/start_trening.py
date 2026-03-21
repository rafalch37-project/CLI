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

    # Pobranie i walidacja parametrów z ankiety
    raw_dni = get_val("dni")
    try:
        dni = int(raw_dni)
        if not (2 <= dni <= 6):
            print(f"   [!] 'dni' = {dni} jest poza zakresem [2–6] — używam domyślnej: 3")
            dni = 3
    except (TypeError, ValueError):
        print(f"   [!] 'dni' ma nieprawidłową wartość ({raw_dni!r}) — używam domyślnej: 3")
        dni = 3

    priorytety = get_val("priorytet") or []

    # Mapowanie nazw z ankiety na klucze w bazie
    map_prio = {
        "Klatka piersiowa": "Klatka",
        "Plecy": "Najszerszy",
        "Nogi": "Czworogłowy",
        "Barki": "Naramienny",
        "Biceps": "Biceps",
        "Triceps": "Triceps"
    }
    prio_mapped = [map_prio.get(p, p) for p in priorytety]

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
        # 1. Próba znalezienia idealnego dopasowania (unikalne)
        opts = [cw for cw in baza_cwiczen if cw['Nazwa_Cwiczenia'] not in used_exercises]
        if muscle: opts = [cw for cw in opts if muscle.lower() in cw['Partia_Glowna'].lower()]
        if type_f: opts = [cw for cw in opts if cw['Typ ćwiczenia'] == type_f]
        if gear_f: opts = [cw for cw in opts if cw['Sprzet'] in gear_f]
        if specific: opts = [cw for cw in opts if specific.lower() in cw['Nazwa_Cwiczenia'].lower()]
        
        # 2. Jeśli brak, poluzuj filtry sprzętu i typu, ale zachowaj unikalność i partię
        if not opts:
            opts = [cw for cw in baza_cwiczen if cw['Nazwa_Cwiczenia'] not in used_exercises]
            if muscle: opts = [cw for cw in opts if muscle.lower() in cw['Partia_Glowna'].lower()]
        
        # 3. Jeśli nadal brak unikalnych dla partii, weź jakiekolwiek unikalne (zabezpieczenie)
        if not opts:
            opts = [cw for cw in baza_cwiczen if cw['Nazwa_Cwiczenia'] not in used_exercises]
            
        # 4. Jeśli cała baza unikalnych wyczerpana (bardzo mało prawdopodobne), weź cokolwiek
        if not opts:
            opts = baza_cwiczen
            
        chosen = random.choice(opts)
        used_exercises.add(chosen['Nazwa_Cwiczenia'])
        return chosen

    plan = []
    
    # --- DYNAMICZNE BUDOWANIE SESJI Z UWZGLĘDNIENIEM PRIORYTETÓW ---
    def build_session(name, base_structure):
        prio_complex = []
        prio_isol = []
        other_complex = []
        other_isol = []
        
        for item in base_structure:
            is_prio = any(p.lower() in item['muscle'].lower() for p in prio_mapped)
            is_complex = item.get('type_f') == 'Wielostawowe' or 'specific' in item
            
            if is_prio:
                if is_complex: prio_complex.append(item)
                else: prio_isol.append(item)
            else:
                if is_complex: other_complex.append(item)
                else: other_isol.append(item)
        
        final_list = prio_complex + prio_isol + other_complex + other_isol
        
        sesja = {"nazwa_sesji": name, "cwiczenia": []}
        for idx, item in enumerate(final_list):
            exclude_keywords = []
            if 'Klatka' in item['muscle'] and idx == 0:
                exclude_keywords = ['triceps', 'barki', 'pionowo']
            
            cw = pick_exercise(muscle=item['muscle'], type_f=item.get('type_f'), gear_f=item.get('gear_f'), specific=item.get('specific'))
            
            if exclude_keywords and any(k in cw['Krótki opis techniki'].lower() for k in exclude_keywords):
                # Ponowne losowanie jest już bezpieczniejsze dzięki poprawionej pick_exercise
                cw = pick_exercise(muscle=item['muscle'], type_f=item.get('type_f'), gear_f=item.get('gear_f'), specific=item.get('specific'))

            is_prio = any(p.lower() in item['muscle'].lower() for p in prio_mapped)
            if is_prio:
                s = 4 if item.get('type_f') == 'Wielostawowe' or idx == 0 else 3
            else:
                s = 3 if item.get('type_f') == 'Wielostawowe' else 2
                
            sesja["cwiczenia"].append({
                "nazwa": cw['Nazwa_Cwiczenia'],
                "serie": s,
                "powtorzenia": "6-10" if cw['Typ ćwiczenia'] == "Wielostawowe" else "10-12",
                "notatki": f"Tempo: {get_smart_tempo(cw['Nazwa_Cwiczenia'])}. {cw['Krótki opis techniki']}"
            })
        return sesja

    # --- SCENARIUSZE ---
    if dni >= 4:
        p1_struct = [
            {'muscle': 'Klatka', 'type_f': 'Wielostawowe'},
            {'muscle': 'Czworogłowy', 'type_f': 'Wielostawowe'},
            {'muscle': 'Naramienny (bok)', 'gear_f': ['Wyciąg']},
            {'muscle': 'Klatka', 'type_f': 'Izolowane'},
            {'muscle': 'Czworogłowy', 'type_f': 'Izolowane'},
            {'muscle': 'Triceps', 'gear_f': ['Wyciąg']}
        ]
        l1_struct = [
            {'muscle': 'Najszerszy', 'specific': 'ściąganie'},
            {'muscle': 'Dwugłowy', 'type_f': 'Wielostawowe'},
            {'muscle': 'Najszerszy', 'specific': 'wiosłowanie'},
            {'muscle': 'Naramienny (tył)'},
            {'muscle': 'Dwugłowy'},
            {'muscle': 'Biceps', 'gear_f': ['Hantle']}
        ]
        p2_struct = [
            {'muscle': 'Klatka', 'gear_f': ['Hantle']},
            {'muscle': 'Czworogłowy', 'specific': 'Przysiad'},
            {'muscle': 'Naramienny', 'gear_f': ['Sztanga', 'Hantle']},
            {'muscle': 'Czworogłowy', 'specific': 'bułgarskie'},
            {'muscle': 'Klatka', 'gear_f': ['Wyciąg']},
            {'muscle': 'Triceps', 'gear_f': ['Hantle']}
        ]
        l2_struct = [
            {'muscle': 'Najszerszy', 'gear_f': ['Drążek']},
            {'muscle': 'Dwugłowy', 'specific': 'Dzień dobry'},
            {'muscle': 'Najszerszy', 'gear_f': ['Hantle']},
            {'muscle': 'Naramienny (tył)'},
            {'muscle': 'Biceps', 'gear_f': ['Sztanga']},
            {'muscle': 'brzucha'}
        ]
        
        plan.append(build_session("PUSH 1 (Priorytety przód)", p1_struct))
        plan.append(build_session("PULL 1 (Priorytety tył)", l1_struct))
        plan.append(build_session("PUSH 2 (Priorytety przód)", p2_struct))
        plan.append(build_session("PULL 2 (Priorytety tył)", l2_struct))

    else:
        push_struct = [
            {'muscle': 'Klatka', 'type_f': 'Wielostawowe'},
            {'muscle': 'Naramienny', 'type_f': 'Wielostawowe'},
            {'muscle': 'Klatka', 'type_f': 'Izolowane'},
            {'muscle': 'Naramienny (bok)', 'type_f': 'Izolowane'},
            {'muscle': 'Triceps', 'gear_f': ['Wyciąg']},
            {'muscle': 'Triceps', 'gear_f': ['Hantle']}
        ]
        pull_struct = [
            {'muscle': 'Najszerszy', 'specific': 'ściąganie'},
            {'muscle': 'Najszerszy', 'specific': 'wiosłowanie'},
            {'muscle': 'Naramienny (tył)'},
            {'muscle': 'Biceps', 'gear_f': ['Sztanga']},
            {'muscle': 'Biceps', 'gear_f': ['Hantle']},
            {'muscle': 'brzucha'}
        ]
        legs_struct = [
            {'muscle': 'Czworogłowy', 'type_f': 'Wielostawowe'},
            {'muscle': 'Dwugłowy', 'type_f': 'Wielostawowe'},
            {'muscle': 'Czworogłowy', 'type_f': 'Izolowane'},
            {'muscle': 'Dwugłowy', 'type_f': 'Izolowane'},
            {'muscle': 'łydki'},
            {'muscle': 'brzucha'}
        ]
        
        plan.append(build_session("PUSH", push_struct))
        plan.append(build_session("PULL", pull_struct))
        plan.append(build_session("LEGS", legs_struct))

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"✅ Skrypt dostosowany do {dni} dni treningowych z uwzględnieniem priorytetów: {', '.join(priorytety)}.")

if __name__ == "__main__":
    run_training_pipeline()
