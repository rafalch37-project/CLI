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
    for p in db:
        if p['Nazwa'].lower() == name_low:
            return p
    for p in db:
        db_name_low = p['Nazwa'].lower()
        if name_low in db_name_low or db_name_low in name_low:
            return p
    return None

def generate_diet_html(jadlospis, produkty_db):
    if not jadlospis: return "<p>Brak danych dietetycznych.</p>", 0, 0, 0, 0
    
    html = ""
    day_b = day_t = day_w = day_kcal = 0
    
    for meal in jadlospis:
        meal_b = meal_t = meal_w = meal_kcal = 0
        
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
            p_data = find_product_in_db(nazwa, produkty_db)
            
            if p_data and waga > 0:
                ratio = waga / 100.0
                b = round(p_data['Bialko'] * ratio, 1)
                t = round(p_data['Tluszcz'] * ratio, 1)
                w = round(p_data['Weglowodany'] * ratio, 1)
                kcal = round(p_data['Kcal'] * ratio, 0)
                
                # Dodajemy do sumy posiłku
                meal_b += b
                meal_t += t
                meal_w += w
                meal_kcal += kcal
            else:
                b = t = w = kcal = "-"

            html += f'      <tr>'
            html += f'        <td>{nazwa}</td>'
            html += f'        <td>{ilosc}</td>'
            html += f'        <td>{b}</td><td>{t}</td><td>{w}</td><td>{kcal}</td>'
            html += f'      </tr>'
            
        # Suma posiłku (DYNAMICZNA)
        html += f'      <tr class="summary-row">'
        html += f'        <td>SUMA POSIŁKU:</td>'
        html += f'        <td>-</td>'
        html += f'        <td>{round(meal_b, 1)}</td>'
        html += f'        <td>{round(meal_t, 1)}</td>'
        html += f'        <td>{round(meal_w, 1)}</td>'
        html += f'        <td>{round(meal_kcal, 0)}</td>'
        html += f'      </tr>'
        html += f'    </tbody>'
        html += f'  </table>'
        if "notatki" in meal and meal["notatki"]:
            html += f'  <div class="notes">{meal["notatki"]}</div>'
        html += f'</div>'
        
        # Dodajemy do sumy dnia
        day_b += meal_b
        day_t += meal_t
        day_w += meal_w
        day_kcal += meal_kcal
        
    return html, round(day_b, 1), round(day_t, 1), round(day_w, 1), round(day_kcal, 0)

def generate_summary_html(b, t, w, kcal, target):
    html = f'''
    <div class="table-container" style="margin-top: 10px; border-top: 2px solid #3b312b; padding-top: 10px;">
        <div class="header" style="font-size: 22px;">PODSUMOWANIE DNIA (REALNE)</div>
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
                    <td>{b} g</td>
                    <td>{t} g</td>
                    <td>{w} g</td>
                    <td>{kcal} kcal</td>
                </tr>
                <tr style="font-size: 11px; color: #777;">
                    <td>Cel: {target.get("B", 0)}g</td>
                    <td>Cel: {target.get("T", 0)}g</td>
                    <td>Cel: {target.get("W", 0)}g</td>
                    <td>Cel: {target.get("kcal", 0)}kcal</td>
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
        
        html = html.replace("{{IMIE}}", imie)
        
        # Generowanie tabel i dynamiczne obliczanie sum
        diet_tables, total_b, total_t, total_w, total_kcal = generate_diet_html(data.get("jadlospis", []), produkty_db)
        html = html.replace("{{DIETA}}", diet_tables)
        
        # Generowanie podsumowania dnia
        target = data.get("makro_target", {})
        target["kcal"] = data.get("kalorie", 0)
        summary_table = generate_summary_html(total_b, total_t, total_w, total_kcal, target)
        html = html.replace("{{PODSUMOWANIE}}", summary_table)

        out_path = os.path.join(output_dir, f"Plan_Dietetyczny_{imie}.html")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"✅ Plan dietetyczny wygenerowany z dynamicznym podliczaniem: {out_path}")

if __name__ == "__main__":
    pack_diet()
