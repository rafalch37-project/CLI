import json
import os
import random

def run_training_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ankieta_path = os.path.join(base_dir, 'ankieta_j.json')
    baza_path = os.path.join(base_dir, '..', 'src', 'baza_cwiczen_j.json')
    output_path = os.path.join(base_dir, 'gotowy_plan_treningowy.json')

    print("1. Ładowanie danych...")
    with open(ankieta_path, 'r', encoding='utf-8') as f:
        ankieta = json.load(f)
    with open(baza_path, 'r', encoding='utf-8') as f:
        baza_cwiczen = json.load(f)

    def get_ans(q):
        for item in ankieta:
            if q.lower() in str(item.get('pytanie', '')).lower():
                return item.get('odpowiedz')
        return None

    # 2. Mapowanie sprzętu
    print("2. Filtrowanie bazy pod kątem dostępnego sprzętu...")
    sprzet_dostepny = {
        "Sztanga": get_ans("Dostęp: Sztanga") == "Tak",
        "Hantle": get_ans("Dostęp: Hantle") == "Tak",
        "Maszyna": get_ans("Dostęp: Maszyna") == "Tak",
        "Wyciąg": get_ans("Dostęp: Wyciąg") == "Tak",
        "Poręcze": get_ans("Dostęp: Poręcze") == "Tak",
        "Drążek": get_ans("Dostęp: Drążek") == "Tak",
        "Ławka": get_ans("Dostęp: Ławka") == "Tak",
        "Talerz": get_ans("Dostęp: Talerz") == "Tak",
        "Masa własna": True
    }

    baza_przefiltrowana = [
        cw for cw in baza_cwiczen 
        if sprzet_dostepny.get(cw.get('Sprzet'), False) or cw.get('Sprzet') == "Masa własna"
    ]

    # 3. Parametry klienta
    dni = int(get_ans("Ile dni w tygodniu") or 3)
    priorytety = [get_ans("Priorytet 1"), get_ans("Priorytet 2")]

    print(f"3. Generowanie planu na {dni} dni...")

    def wybierz_cwiczenia(partia, liczba=1):
        opcje = [cw for cw in baza_przefiltrowana if partia.lower() in cw['Partia_Glowna'].lower()]
        opcje.sort(key=lambda x: 0 if x['Typ ćwiczenia'] == 'Wielostawowe' else 1)
        return opcje[:liczba]

    plan = {}

    if dni <= 2:
        for i in range(1, dni + 1):
            nazwa = f"Dzień {i}: FBW (Całe ciało)"
            plan[nazwa] = []
            plan[nazwa].extend(wybierz_cwiczenia("Nogi", 2))
            plan[nazwa].extend(wybierz_cwiczenia("Plecy", 2))
            plan[nazwa].extend(wybierz_cwiczenia("Klatka", 1))
            plan[nazwa].extend(wybierz_cwiczenia("Barki", 1))
            plan[nazwa].extend(wybierz_cwiczenia("Biceps", 1))
            plan[nazwa].extend(wybierz_cwiczenia("Triceps", 1))

    elif dni == 3:
        plan["Dzień 1: PUSH (Klatka, Barki, Triceps)"] = wybierz_cwiczenia("Klatka", 2) + wybierz_cwiczenia("Naramienny", 2) + wybierz_cwiczenia("Triceps", 1)
        plan["Dzień 2: PULL (Plecy, Tył barku, Biceps)"] = wybierz_cwiczenia("Plecy", 3) + wybierz_cwiczenia("Biceps", 1)
        plan["Dzień 3: LEGS (Nogi, Brzuch)"] = wybierz_cwiczenia("Czworogłowy", 2) + wybierz_cwiczenia("Dwugłowy", 1) + wybierz_cwiczenia("Łydki", 1) + wybierz_cwiczenia("Brzuch", 1)

    elif dni >= 4:
        for i in range(1, (dni // 2) + 1):
            u_name = f"Dzień {i*2-1}: UPPER (Góra ciała)"
            l_name = f"Dzień {i*2}: LOWER (Dół ciała)"
            plan[u_name] = wybierz_cwiczenia("Klatka", 2) + wybierz_cwiczenia("Plecy", 2) + wybierz_cwiczenia("Naramienny", 1) + wybierz_cwiczenia("Biceps", 1) + wybierz_cwiczenia("Triceps", 1)
            plan[l_name] = wybierz_cwiczenia("Czworogłowy", 2) + wybierz_cwiczenia("Dwugłowy", 2) + wybierz_cwiczenia("Łydki", 1) + wybierz_cwiczenia("Brzuch", 1)
        if dni % 2 != 0:
            plan[f"Dzień {dni}: FBW/Extra"] = wybierz_cwiczenia("Klatka", 1) + wybierz_cwiczenia("Plecy", 1) + wybierz_cwiczenia("Nogi", 1) + wybierz_cwiczenia("Brzuch", 1)

    # Budowanie finalnego formatu
    final_plan = []
    for dzien, cwiczenia in plan.items():
        sesja = {"nazwa_sesji": dzien, "cwiczenia": []}
        for cw in cwiczenia:
            is_priority = any(p and p.lower() in cw['Partia_Glowna'].lower() for p in priorytety if p)
            serie = 4 if is_priority else 3
            sesja["cwiczenia"].append({
                "nazwa": cw['Nazwa_Cwiczenia'],
                "partia": cw['Partia_Glowna'],
                "serie": serie,
                "powtorzenia": "6-10" if cw['Typ ćwiczenia'] == 'Wielostawowe' else "10-12",
                "tempo": "3-1-1-0",
                "notatki": cw['Krótki opis techniki']
            })
        final_plan.append(sesja)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_plan, f, indent=2, ensure_ascii=False)

    print(f"\n--- GOTOWE: Plan na {dni} dni wygenerowany w {output_path} ---")

if __name__ == "__main__":
    run_training_pipeline()
