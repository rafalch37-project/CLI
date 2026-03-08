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

    # Obliczenia Celów
    waga = float(get_ans("waga", "Waga") or 80)
    wzrost = float(get_ans("wzrost", "Wzrost") or 180)
    wiek = int(get_ans("wiek", "Wiek") or 30)
    plec = str(get_ans("plec", "Płeć") or "Mężczyzna").lower()
    cel = str(get_ans("cel", "Główny cel") or "utrzymanie").lower()
    aktywnosc = str(get_ans("aktywnosc", "Aktywność") or "średnia").lower()

    pal = 1.6 if "średnia" in aktywnosc or "rekompozycja" in cel else (1.8 if "wysoka" in aktywnosc else 1.4)
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
