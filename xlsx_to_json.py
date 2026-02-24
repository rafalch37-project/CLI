import pandas as pd
import json

def convert_xlsx_to_json(excel_file, json_file):
    try:
        # Wczytanie pliku Excel
        df = pd.read_excel(excel_file)
        
        # Mapowanie nazw kolumn na klucze JSON (zgodnie z ankieta_j.json)
        # Zakładamy, że kolumny w Excelu to: 'Pytanie / Kategoria', 'Odpowiedź klienta', 'Znaczenie dla planu treningowego'
        mapping = {
            'Pytanie / Kategoria': 'pytanie',
            'Odpowiedź klienta': 'odpowiedz',
            'Znaczenie dla planu treningowego': 'znaczenie'
        }
        
        # Zmiana nazw kolumn
        df = df.rename(columns=mapping)
        
        # Konwersja na listę słowników (JSON)
        # fillna(None) zamienia puste pola w Excelu (NaN) na null w JSON
        data = df.to_dict(orient='records')
        
        # Zapis do pliku JSON z zachowaniem polskich znaków
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"Sukces! Dane z {excel_file} zostały zapisane do {json_file}.")
        
    except Exception as e:
        print(f"Wystąpił błąd: {e}")

if __name__ == "__main__":
    convert_xlsx_to_json('ankieta.xlsx', 'ankieta_j.json')
