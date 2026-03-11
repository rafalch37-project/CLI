import json
import os

def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def generate_training_html(plan_data):
    if not plan_data: return "<p>Brak danych treningowych.</p>"
    
    html = ""
    for session in plan_data:
        html += f'<div class="table-container">'
        html += f'  <div class="header">{session["nazwa_sesji"]}</div>'
        html += f'  <table>'
        html += f'    <thead>'
        html += f'      <tr>'
        html += f'        <th>Nazwa Ćwiczenia</th>'
        html += f'        <th class="serie-col">Serie</th>'
        html += f'        <th class="powt-col">Powtórzenia</th>'
        html += f'      </tr>'
        html += f'    </thead>'
        html += f'    <tbody>'
        for cw in session["cwiczenia"]:
            html += f'      <tr>'
            html += f'        <td>'
            html += f'          <span class="exercise-name">{cw["nazwa"]}</span>'
            html += f'          <span class="notes">{cw["notatki"]}</span>'
            html += f'        </td>'
            html += f'        <td class="serie-col">{cw["serie"]}</td>'
            html += f'        <td class="powt-col">{cw["powtorzenia"]}</td>'
            html += f'      </tr>'
        html += f'    </tbody>'
        html += f'  </table>'
        html += f'</div>'
    return html

def pack_plans():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ścieżki zaktualizowane do nowej struktury folderu 'master'
    dieta_json = os.path.join(base_dir, '..', 'ankieta_dieta', 'gotowe_dane_klienta.json')
    trening_json = os.path.join(base_dir, '..', 'ankieta_trening', 'gotowy_plan_treningowy.json')
    szablon_trening_path = os.path.join(base_dir, 'szablon_trening_master.html')
    output_dir = os.path.join(base_dir, '..', 'plany')

    if not os.path.exists(output_dir): os.makedirs(output_dir)

    data_c = load_json(dieta_json)
    data_t = load_json(trening_json)

    if not data_c or not data_t:
        print("❌ Błąd: Brak wymaganych plików JSON w ankietach.")
        return

    imie = data_c.get("imie", "Klient")
    print(f"--- PAKOWANIE PLANU TRENINGOWEGO DLA: {imie} ---")

    if os.path.exists(szablon_trening_path):
        with open(szablon_trening_path, 'r', encoding='utf-8') as f:
            html_t = f.read()
        
        html_t = html_t.replace("{{IMIE}}", imie)
        training_tables = generate_training_html(data_t)
        html_t = html_t.replace("{{TRENING}}", training_tables)

        out_t_path = os.path.join(output_dir, f"Plan_Treningowy_{imie}.html")
        with open(out_t_path, 'w', encoding='utf-8') as f:
            f.write(html_t)
        print(f"✅ Plan treningowy wygenerowany: {out_t_path}")

if __name__ == "__main__":
    pack_plans()
