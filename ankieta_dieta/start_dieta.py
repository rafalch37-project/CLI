import pandas as pd
import json
import os

def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ankieta_json_path = os.path.join(base_dir, 'ankieta_j.json')
    output_json_path = os.path.join(base_dir, 'gotowe_dane_klienta.json')

    try:
        with open(ankieta_json_path, 'r', encoding='utf-8') as f:
            ankieta = json.load(f)
    except Exception as e:
        print(f"   [!] Błąd odczytu: {e}")
        return

    def get_ans(key, search_term):
        if isinstance(ankieta, dict): return ankieta.get(key)
        if isinstance(ankieta, list):
            for item in ankieta:
                if search_term.lower() in str(item.get('pytanie', '')).lower():
                    return item.get('odpowiedz')
        return None

    def validate_float(value, name, min_val, max_val, default):
        try:
            v = float(value)
        except (TypeError, ValueError):
            print(f"   [!] '{name}' ma nieprawidłową wartość ({value!r}) — używam domyślnej: {default}")
            return default
        if not (min_val <= v <= max_val):
            print(f"   [!] '{name}' = {v} jest poza zakresem [{min_val}–{max_val}] — używam domyślnej: {default}")
            return default
        return v

    def validate_int(value, name, min_val, max_val, default):
        try:
            v = int(value)
        except (TypeError, ValueError):
            print(f"   [!] '{name}' ma nieprawidłową wartość ({value!r}) — używam domyślnej: {default}")
            return default
        if not (min_val <= v <= max_val):
            print(f"   [!] '{name}' = {v} jest poza zakresem [{min_val}–{max_val}] — używam domyślnej: {default}")
            return default
        return v

    def validate_choice(value, name, valid_options, default):
        v = str(value or "").lower().strip()
        if not any(opt in v for opt in valid_options):
            print(f"   [!] '{name}' = '{value}' — nieznana wartość (dopuszczalne: {valid_options}) — używam domyślnej: '{default}'")
            return default
        return v

    # Obliczenia Celów
    waga    = validate_float(get_ans("waga", "Waga"),         "waga",       30,  300, 80)
    wzrost  = validate_float(get_ans("wzrost", "Wzrost"),     "wzrost",    100,  250, 180)
    wiek    = validate_int  (get_ans("wiek", "Wiek"),         "wiek",       10,  100, 30)
    plec      = validate_choice(get_ans("plec", "Płeć"),      "plec", ["m", "k"], "mężczyzna")
    cel       = validate_choice(get_ans("cel", "Główny cel"), "cel",  ["redukcja", "masa", "budowa", "utrzymanie", "rekompozycja"], "utrzymanie")
    aktywnosc = str(get_ans("aktywnosc", "Aktywność") or "").lower()  # wolny tekst z ankiety

    pal = 1.8 if "wysoka" in aktywnosc else (1.6 if "średnia" in aktywnosc else 1.4)
    bmr = (10 * waga) + (6.25 * wzrost) - (5 * wiek) + (5 if "m" in plec else -161)
    tdee = bmr * pal
    final_kcal = tdee - 300 if "redukcja" in cel else (tdee + 300 if "masa" in cel or "budowa" in cel else tdee)
    
    bialko_target = round(waga * 2.1) # Lekko wyższe białko zgodnie z trendami sportowymi
    tluszcz_target = round(waga * 0.8)
    wegle_target = round((final_kcal - (bialko_target * 4) - (tluszcz_target * 9)) / 4)

    dane_final = {
        "imie": get_ans("imie", "Imię") or "Klient",
        "kalorie": round(final_kcal),
        "makro_target": {
            "B": bialko_target,
            "T": tluszcz_target,
            "W": wegle_target
        },
        "jadlospis": [] # Puste - tu wkraczam ja (Gemini)
    }

    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(dane_final, f, indent=2, ensure_ascii=False)
    
    print(f"--- GOTOWE: Cele wyliczone (Kcal: {dane_final['kalorie']}). Czas na ułożenie menu przez Gemini. ---")

if __name__ == "__main__":
    run_pipeline()
