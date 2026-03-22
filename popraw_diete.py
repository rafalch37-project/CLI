#!/usr/bin/env python3
"""
popraw_diete.py — Korekta jadlospisu bez generowania od nowa
Uzycie: python popraw_diete.py <folder_klienta> "opis zmian"

Przyklad:
  python popraw_diete.py "Beata_Chmielowska_2026-03-22" "zamien kurczaka w posilku 2 na lososia"
"""

import json
import os
import re
import sys
import difflib

from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── pomocnicze funkcje HTML (skopiowane z utworz_klienta.py) ──────────────

def _get_weight(ilosc_str):
    match = re.search(r'(\d+)\s*g', str(ilosc_str).lower())
    return float(match.group(1)) if match else 0.0

def _normalize(name):
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'[^a-ząćęłńóśźż0-9\s]', ' ', name.lower())
    return ' '.join(name.split())

def find_product(name, db):
    nc = _normalize(name)
    normed = [(p, _normalize(p["Nazwa"])) for p in db]
    for p, pn in normed:
        if p["Nazwa"].lower().strip() == name.lower().strip(): return p
    for p, pn in normed:
        if pn == nc: return p
    for p, pn in normed:
        if nc in pn or pn in nc: return p
    qw = set(nc.split())
    for p, pn in normed:
        if qw and qw.issubset(set(pn.split())): return p
    matches = difflib.get_close_matches(nc, [pn for _, pn in normed], n=1, cutoff=0.6)
    if matches:
        for p, pn in normed:
            if pn == matches[0]: return p
    return None

def generate_diet_html(jadlospis, produkty_db):
    if not jadlospis:
        return "<p>Brak danych.</p>", 0, 0, 0, 0
    html = ""
    day_b = day_t = day_w = day_kcal = 0
    for meal in jadlospis:
        mb = mt = mw = mk = 0
        html += f'<div class="table-container">'
        html += f'  <div class="header">{meal.get("nazwa_posilku","Posiłek")}</div>'
        html += '  <table><thead><tr>'
        html += '    <th>Produkt</th><th style="width:25%">Ilość</th>'
        html += '    <th style="width:10%">B</th><th style="width:10%">T</th>'
        html += '    <th style="width:10%">W</th><th style="width:12%">Kcal</th>'
        html += '  </tr></thead><tbody>'
        for item in meal.get("skladniki", []):
            nazwa = item.get("Produkt", "-")
            ilosc = item.get("Ilość",   "-")
            waga  = _get_weight(ilosc)
            pd    = find_product(nazwa, produkty_db)
            if pd and waga > 0:
                r = waga / 100.0
                b = round(pd["Bialko"]      * r, 1)
                t = round(pd["Tluszcz"]     * r, 1)
                w = round(pd["Weglowodany"] * r, 1)
                k = round(pd["Kcal"]        * r, 0)
                mb += b; mt += t; mw += w; mk += k
            else:
                b = t = w = k = "-"
            html += (f'      <tr><td>{nazwa}</td><td>{ilosc}</td>'
                     f'<td>{b}</td><td>{t}</td><td>{w}</td><td>{k}</td></tr>')
        html += (f'      <tr class="summary-row"><td>SUMA POSIŁKU:</td><td>-</td>'
                 f'<td>{round(mb,1)}</td><td>{round(mt,1)}</td>'
                 f'<td>{round(mw,1)}</td><td>{round(mk,0)}</td></tr>')
        html += '  </tbody></table>'
        if meal.get("notatki"):
            html += f'  <div class="notes">{meal["notatki"]}</div>'
        html += '</div>'
        day_b += mb; day_t += mt; day_w += mw; day_kcal += mk
    return html, round(day_b,1), round(day_t,1), round(day_w,1), round(day_kcal,0)

def generate_summary_html(b, t, w, kcal, target):
    k_b = b*4; k_t = t*9; k_w = w*4
    total = k_b + k_t + k_w
    pct_b = round((k_b/total)*100,1) if total > 0 else 0
    pct_t = round((k_t/total)*100,1) if total > 0 else 0
    pct_w = round((k_w/total)*100,1) if total > 0 else 0
    diff_b = round(b - target.get("B",0),1)
    diff_t = round(t - target.get("T",0),1)
    diff_w = round(w - target.get("W",0),1)
    diff_k = round(kcal - target.get("kcal",0),1)
    return f'''
    <div class="table-container" style="margin-top:10px;border-top:2px solid #3b312b;padding-top:10px;">
        <div class="header" style="font-size:22px;">PODSUMOWANIE DNIA (REALNE)</div>
        <table><thead><tr>
            <th style="width:25%">Białko (B)</th>
            <th style="width:25%">Tłuszcze (T)</th>
            <th style="width:25%">Węglowodany (W)</th>
            <th style="width:25%">Kalorie (Kcal)</th>
        </tr></thead>
        <tbody><tr style="font-size:18px;font-weight:600;">
            <td>{b} g</td><td>{t} g</td><td>{w} g</td><td>{kcal} kcal</td>
        </tr></tbody></table>
        <div class="macro-bar-container">
            <div title="Białko"      style="width:{pct_b}%;background:#3498db;"></div>
            <div title="Tłuszcze"    style="width:{pct_t}%;background:#f1c40f;"></div>
            <div title="Węglowodany" style="width:{pct_w}%;background:#e67e22;"></div>
        </div>
        <div class="macro-label-container">
            <span>Białko: {int(pct_b)}%</span>
            <span>Tłuszcze: {int(pct_t)}%</span>
            <span>Węglowodany: {int(pct_w)}%</span>
        </div>
        <!-- Cel: {target.get("B",0)}g B | {target.get("T",0)}g T | {target.get("W",0)}g W | {target.get("kcal",0)} kcal
             Roznica: {diff_b:+}g B | {diff_t:+}g T | {diff_w:+}g W | {diff_k:+} kcal -->
    </div>'''

def pack_html(dane_klienta, produkty_db, output_dir):
    szablon = os.path.join(BASE_DIR, "master", "szablon_dieta_master.html")
    if not os.path.exists(szablon):
        print("  [!] Brak szablonu szablon_dieta_master.html")
        return ""
    with open(szablon, "r", encoding="utf-8") as f:
        html = f.read()
    imie = dane_klienta.get("imie", "Klient")
    html = html.replace("{{IMIE}}", imie)
    diet_tables, tb, tt, tw, tk = generate_diet_html(dane_klienta.get("jadlospis", []), produkty_db)
    html = html.replace("{{DIETA}}", diet_tables)
    target = dict(dane_klienta.get("makro_target", {}))
    target["kcal"] = dane_klienta.get("kalorie", 0)
    html = html.replace("{{PODSUMOWANIE}}", generate_summary_html(tb, tt, tw, tk, target))
    imie_safe = re.sub(r'[^\w\s-]', '', imie).strip().replace(' ', '_')
    out_path = os.path.join(output_dir, f"Plan_Dietetyczny_{imie_safe}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return out_path


# ── główna logika ──────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("\n  Uzycie:  python popraw_diete.py <folder_klienta> \"opis zmian\"")
        print("  Przyklad: python popraw_diete.py \"Beata_Chmielowska_2026-03-22\" \"zamien kurczaka na lososia w posilku 2\"")
        print()
        print("  Dostepni klienci:")
        klienci_dir = os.path.join(BASE_DIR, "klienci")
        if os.path.exists(klienci_dir):
            for f in os.listdir(klienci_dir):
                print(f"    - {f}")
        sys.exit(1)

    folder_klienta = sys.argv[1]
    korekta        = sys.argv[2]

    client_dir = os.path.join(BASE_DIR, "klienci", folder_klienta)
    if not os.path.exists(client_dir):
        print(f"\n  [BLAD] Folder nie istnieje: {client_dir}")
        print("  Dostepni klienci:")
        for f in os.listdir(os.path.join(BASE_DIR, "klienci")):
            print(f"    - {f}")
        sys.exit(1)

    dane_path = os.path.join(client_dir, "dane_klienta.json")
    if not os.path.exists(dane_path):
        print(f"  [BLAD] Brak pliku dane_klienta.json w folderze {folder_klienta}")
        sys.exit(1)

    with open(dane_path, "r", encoding="utf-8") as f:
        dane_klienta = json.load(f)

    produkty_path = os.path.join(BASE_DIR, "src", "produkty.json")
    with open(produkty_path, "r", encoding="utf-8") as f:
        produkty_db = json.load(f)

    # Sprawdz klucz API
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("  [BLAD] Brak klucza GEMINI_API_KEY.")
        sys.exit(1)

    # Wczytaj system prompt
    system_path = os.path.join(BASE_DIR, "src", "system_prompt_diet.md")
    with open(system_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    # Przygotuj liste produktow
    products_lines = [
        f"- {p['Nazwa']}: B={p['Bialko']}g T={p['Tluszcz']}g W={p['Weglowodany']}g Kcal={p['Kcal']} (na 100g)"
        for p in produkty_db
    ]

    aktualny_jadlospis = json.dumps(dane_klienta.get("jadlospis", []), ensure_ascii=False, indent=2)

    prompt = f"""{system_prompt}

---

Masz gotowy jadlospis klienta. Wprowadz do niego TYLKO opisane zmiany, reszta zostaje bez zmian.

DANE KLIENTA:
- Imie: {dane_klienta['imie']}
- Cel kaloryczny: {dane_klienta['kalorie']} kcal
- Bialko: {dane_klienta['makro_target']['B']}g
- Tluszcze: {dane_klienta['makro_target']['T']}g
- Weglowodany: {dane_klienta['makro_target']['W']}g

AKTUALNY JADLOSPIS (JSON):
{aktualny_jadlospis}

BAZA PRODUKTOW — uzywaj WYLACZNIE tych produktow:
{chr(10).join(products_lines)}

ZMIANY DO WPROWADZENIA:
{korekta}

ZASADY:
1. Wprowadz TYLKO opisane zmiany — nie zmieniaj niczego innego
2. Dostosuj gramature zmienionych skladnikow zeby makra pozostaly podobne
3. Zachowaj logike kulinarna (jedno zrodlo bialka na posilek, skyr/twarog nie z miesem itp.)
4. Zwroc WYLACZNIE czysty JSON bez markdown:

{{"jadlospis": [...]}}"""

    print(f"\n  Klient: {dane_klienta['imie'].strip()}")
    print(f"  Korekta: {korekta}")
    print("\n  [AI] Wprowadzam zmiany przez Gemini...\n")

    try:
        gemini_client = genai.Client(api_key=api_key)
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        full_text = response.text
    except Exception as e:
        print(f"  [BLAD] Gemini API: {e}")
        sys.exit(1)

    # Parsowanie JSON
    nowy_jadlospis = None
    for attempt in [
        lambda t: json.loads(t.strip()),
        lambda t: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', t).group(1)),
        lambda t: json.loads(re.search(r'\{[\s\S]*\}', t).group(0)),
    ]:
        try:
            data = attempt(full_text)
            nowy_jadlospis = data.get("jadlospis", [])
            if nowy_jadlospis:
                break
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    if not nowy_jadlospis:
        print("  [BLAD] Nie udalo sie sparsowac odpowiedzi Gemini.")
        sys.exit(1)

    # Zapisz zaktualizowany JSON
    dane_klienta["jadlospis"] = nowy_jadlospis
    with open(dane_path, "w", encoding="utf-8") as f:
        json.dump(dane_klienta, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Zaktualizowano: {dane_path}")

    # Przepakuj HTML
    html_path = pack_html(dane_klienta, produkty_db, client_dir)
    if html_path:
        print(f"  [OK] HTML przepakowany: {html_path}")

    print("\n  Gotowe!\n")


if __name__ == "__main__":
    main()
