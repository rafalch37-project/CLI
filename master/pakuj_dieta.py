import json
import os
import re

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def get_weight(ilosc_str):
    """Wyciąga liczbę gramów z ciągu znaków np. '150g (2 sztuki)' -> 150"""
    match = re.search(r'(\d+)\s*g', ilosc_str.lower())
    if match:
        return float(match.group(1))
    return 0

def find_product_in_db(name, db):
    """Szuka produktu w bazie, ignorując wielkość liter i dopiski w nawiasach"""
    name_low = name.lower().strip()
    
    # 1. Szukamy dokładnego dopasowania
    for p in db:
        if p['Nazwa'].lower() == name_low:
            return p
            
    # 2. Szukamy dopasowania "zawiera się" (np. "Pierś z kurczaka" pasuje do "Pierś z kurczaka (surowa)")
    for p in db:
        db_name_low = p['Nazwa'].lower()
        if name_low in db_name_low or db_name_low in name_low:
            return p
            
    return None

def generate_diet_html(jadlospis, produkty_db):
    if not jadlospis: return "<p>Brak danych dietetycznych.</p>"
    
    html = ""
    for meal in jadlospis:
        html += f'<div class="table-container">'
        html += f'  <div class="header">{meal.get("nazwa_posilku", "Posiłek")}</div>'
        html += f'  <table>'
        html += f'    <thead>'
        html += f'      <tr>'
        html += f'        <th>Produkt / Składnik</th>'
        html += f'        <th style="width: 25%">Ilość / Waga</th>'
        html += f'        <th style="width: 10%">B (g)</th>'
        html += f'        <th style="width: 10%">T (g)</th>'
        html += f'        <th style="width: 10%">W (g)</th>'
        html += f'        <th style="width: 12%">Kcal</th>'
        html += f'      </tr>'
        html += f'    </thead>'
        html += f'    <tbody>'
        
        for item in meal.get("skladniki", []):
            nazwa = item.get("Produkt", "-")
            ilosc = item.get("Ilość", "-")
            waga = get_weight(ilosc)
            
            # Szukamy w bazie inteligentnie
            p_data = find_product_in_db(nazwa, produkty_db)
            
            if p_data and waga > 0:
                ratio = waga / 100.0
                b = round(p_data['Bialko'] * ratio, 1)
                t = round(p_data['Tluszcz'] * ratio, 1)
                w = round(p_data['Weglowodany'] * ratio, 1)
                kcal = round(p_data['Kcal'] * ratio, 0)
            else:
                b = t = w = kcal = "-"

            html += f'      <tr>'
            html += f'        <td>{nazwa}</td>'
            html += f'        <td>{ilosc}</td>'
            html += f'        <td>{b}</td><td>{t}</td><td>{w}</td><td>{kcal}</td>'
            html += f'      </tr>'
            
        html += f'      <tr class="summary-row">'
        html += f'        <td>SUMA POSIŁKU:</td>'
        html += f'        <td>-</td>'
        html += f'        <td>{meal.get("B", 0)}</td>'
        html += f'        <td>{meal.get("T", 0)}</td>'
        html += f'        <td>{meal.get("W", 0)}</td>'
        html += f'        <td>{meal.get("kcal", 0)}</td>'
        html += f'      </tr>'
        html += f'    </tbody>'
        html += f'  </table>'
        if "notatki" in meal and meal["notatki"]:
            html += f'  <div class="notes">{meal["notatki"]}</div>'
        html += f'</div>'
    return html

def generate_summary_html(target, total_kcal):
    html = f'''
    <div class="table-container" style="margin-top: 10px; border-top: 2px solid #3b312b; padding-top: 10px;">
        <div class="header" style="font-size: 22px;">PODSUMOWANIE DNIA (TARGET)</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 25%">Białko (B)</th>
                    <th style="width: 25%">Tłuszcze (T)</th>
                    <th style="width: 25%">Węglowodany (W)</th>
                    <th style="width: 25%">Kalorie (Kcal)</th>
                </tr>
            </thead>
            <tbody>
                <tr style="font-size: 18px; font-weight: 600;">
                    <td>{target.get("B", 0)} g</td>
                    <td>{target.get("T", 0)} g</td>
                    <td>{target.get("W", 0)} g</td>
                    <td>{total_kcal} kcal</td>
                </tr>
            </tbody>
        </table>
    </div>
    '''
    return html

def pack_diet():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dieta_json = os.path.join(base_dir, '..', 'ankieta_dieta', 'gotowe_dane_klienta.json')
    produkty_json = os.path.join(base_dir, '..', 'src', 'produkty.json')
    szablon_path = os.path.join(base_dir, 'szablon_dieta_master.html')
    output_dir = os.path.join(base_dir, '..', 'plany')

    if not os.path.exists(output_dir): os.makedirs(output_dir)

    data = load_json(dieta_json)
    produkty_db = load_json(produkty_json)
    
    if not data or not produkty_db:
        print("❌ Błąd: Brak plików JSON.")
        return

    imie = data.get("imie", "Klient")
    print(f"--- GENEROWANIE PLANU DIETETYCZNEGO DLA: {imie} ---")

    if os.path.exists(szablon_path):
        with open(szablon_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Podstawowe dane
        html = html.replace("{{IMIE}}", imie)
        
        # Posiłki
        diet_tables = generate_diet_html(data.get("jadlospis", []), produkty_db)
        html = html.replace("{{DIETA}}", diet_tables)
        
        # Podsumowanie
        summary_table = generate_summary_html(data.get("makro_target", {}), data.get("kalorie", 0))
        html = html.replace("{{PODSUMOWANIE}}", summary_table)

        out_path = os.path.join(output_dir, f"Plan_Dietetyczny_{imie}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ Plan dietetyczny wygenerowany: {out_path}")

if __name__ == "__main__":
    pack_diet()
