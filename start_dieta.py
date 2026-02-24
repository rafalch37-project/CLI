import pandas as pd
import json
import os

def run_pipeline():
    print("1. Pobieranie danych (Excel lub JSON)...")
    ankieta = []
    
    # Próba odczytu z Excela
    try:
        if os.path.exists('ankieta.xlsx'):
            df = pd.read_excel('ankieta.xlsx')
            mapping = {'Pytanie / Kategoria': 'pytanie', 'Odpowiedź klienta': 'odpowiedz'}
            df = df.rename(columns=mapping)
            ankieta = df.to_dict(orient='records')
            
            # Sprawdzenie czy Excel nie jest pusty (czy Waga ma wartość)
            test_val = next((item['odpowiedz'] for item in ankieta if "Waga" in str(item.get('pytanie', ''))), None)
            if pd.isna(test_val) or test_val is None:
                print("   [!] Excel jest pusty, pobieram dane z ankieta_j.json...")
                with open('ankieta_j.json', 'r', encoding='utf-8') as f:
                    ankieta = json.load(f)
        else:
            with open('ankieta_j.json', 'r', encoding='utf-8') as f:
                ankieta = json.load(f)
    except Exception as e:
        print(f"   [!] Błąd odczytu: {e}. Używam ankieta_j.json.")
        with open('ankieta_j.json', 'r', encoding='utf-8') as f:
            ankieta = json.load(f)

    # Funkcja pomocnicza
    def get_ans(q):
        for item in ankieta:
            if q.lower() in str(item.get('pytanie', '')).lower():
                val = item.get('odpowiedz')
                return val if not pd.isna(val) else None
        return None

    print("2. Obliczam zapotrzebowanie...")
    try:
        waga = float(get_ans("Waga") or 80)
        wzrost = float(get_ans("Wzrost") or 180)
        wiek = int(get_ans("Wiek") or 30)
        plec = str(get_ans("Płeć") or "Mężczyzna").lower()
        cel = str(get_ans("Główny cel") or "utrzymanie").lower()
        aktywnosc = str(get_ans("Aktywność") or "średnia").lower()

        # PAL i BMR (Mifflin-St Jeor)
        pal = 1.6 if "średnia" in aktywnosc else (1.8 if "wysoka" in aktywnosc else 1.4)
        bmr = (10 * waga) + (6.25 * wzrost) - (5 * wiek) + (5 if "m" in plec else -161)
        tdee = bmr * pal
        
        final_kcal = tdee - 300 if "redukcja" in cel else (tdee + 300 if "masa" in cel or "budowa" in cel else tdee)
        bialko, tluszcz = round(waga * 2), round(waga * 0.8)
        wegle = round((final_kcal - (bialko * 4) - (tluszcz * 9)) / 4)

        dane_final = {
            "imie": get_ans("Imię") or "Klient",
            "cel": cel,
            "kalorie": round(final_kcal),
            "makro": {"B": bialko, "T": tluszcz, "W": wegle},
            "info_dodatkowe": get_ans("kontuzje")
        }

        with open('gotowe_dane_klienta.json', 'w', encoding='utf-8') as f:
            json.dump(dane_final, f, indent=2, ensure_ascii=False)

        print(f"\n--- GOTOWE: {dane_final['imie']} ---")
        print(f"Target: {dane_final['kalorie']} kcal | B:{bialko}g T:{tluszcz}g W:{wegle}g")
    except Exception as e:
        print(f"BŁĄD OBLICZEŃ: {e}")

if __name__ == "__main__":
    run_pipeline()
