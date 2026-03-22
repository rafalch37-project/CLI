#!/usr/bin/env python3
"""
utworz_klienta.py — One-Click Pipeline
Użycie: python utworz_klienta.py <sciezka_do_ankiety.json>

Flow:
  1. Wczytaj plik JSON z Ankieta_Premium.html
  2. Zapytaj o typ planu (trening / dieta / oba)
  3. Utwórz folder: klienci/<Imie_Nazwisko>_<data>/
  4. Jeśli trening → generuj plan z bazy ćwiczeń → zapisz HTML
  5. Jeśli dieta  → oblicz makra → Gemini generuje jadłospis → zapisz HTML
"""

import json
import os
import re
import sys
import random
import difflib
from datetime import date

from google import genai

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ══════════════════════════════════════════════════════════════════════════
# SEKCJA 1 — OBLICZENIA DIETETYCZNE (logika z start_dieta.py)
# ══════════════════════════════════════════════════════════════════════════

def oblicz_makra(ankieta: dict) -> dict:
    """Liczy TDEE, kalorie i makroskładniki z ankiety klienta."""

    def vf(key, name, lo, hi, default):
        try:
            v = float(ankieta.get(key, default))
        except (TypeError, ValueError):
            print(f"   [!] '{name}' — nieprawidłowa wartość, używam domyślnej: {default}")
            return float(default)
        if not (lo <= v <= hi):
            print(f"   [!] '{name}' = {v} poza zakresem [{lo}–{hi}], używam domyślnej: {default}")
            return float(default)
        return v

    def vi(key, name, lo, hi, default):
        try:
            v = int(ankieta.get(key, default))
        except (TypeError, ValueError):
            print(f"   [!] '{name}' — nieprawidłowa wartość, używam domyślnej: {default}")
            return int(default)
        if not (lo <= v <= hi):
            print(f"   [!] '{name}' = {v} poza zakresem [{lo}–{hi}], używam domyślnej: {default}")
            return int(default)
        return v

    waga   = vf("waga",   "waga",   30, 300, 80)
    wzrost = vf("wzrost", "wzrost", 100, 250, 180)
    wiek   = vi("wiek",   "wiek",   10, 100, 30)

    plec      = str(ankieta.get("plec", "") or "").lower()
    cel       = str(ankieta.get("cel",  "") or "").lower()
    aktywnosc = str(ankieta.get("aktywnosc", "") or "").lower()

    pal = 1.8 if "wysoka" in aktywnosc else (1.6 if "średnia" in aktywnosc or "srednia" in aktywnosc else 1.4)
    jest_mezczyzna = "m" in plec and "kobieta" not in plec
    bmr  = (10 * waga) + (6.25 * wzrost) - (5 * wiek) + (5 if jest_mezczyzna else -161)
    tdee = bmr * pal

    if "redukcja" in cel:
        final_kcal = tdee - 300
    elif "masa" in cel or "budowa" in cel:
        final_kcal = tdee + 300
    else:
        final_kcal = tdee

    bialko  = round(waga * 2.1)
    tluszcz = round(waga * 0.8)
    wegle   = round((final_kcal - (bialko * 4) - (tluszcz * 9)) / 4)

    return {
        "imie":         ankieta.get("imie", "Klient"),
        "kalorie":      round(final_kcal),
        "makro_target": {"B": bialko, "T": tluszcz, "W": wegle},
        "cel":          cel,
        "kontuzje":     ankieta.get("kontuzje", "brak") or "brak",
        "aktywnosc":    aktywnosc,
        "jadlospis":    []
    }

# ══════════════════════════════════════════════════════════════════════════
# SEKCJA 2 — GENEROWANIE JADŁOSPISU (Claude Opus API)
# ══════════════════════════════════════════════════════════════════════════

def generate_jadlospis(dane_klienta: dict, produkty_db: list) -> list:
    """Wywołuje Gemini API i zwraca listę posiłków jako JSON."""

    system_path = os.path.join(BASE_DIR, "src", "system_prompt_diet.md")
    with open(system_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    products_lines = [
        f"- {p['Nazwa']}: B={p['Bialko']}g T={p['Tluszcz']}g W={p['Weglowodany']}g Kcal={p['Kcal']} (na 100g)"
        for p in produkty_db
    ]

    prompt = f"""{system_prompt}

---

Wygeneruj kompletny jadłospis na 1 dzień dla klienta.

DANE KLIENTA:
- Imię: {dane_klienta['imie']}
- Cel kaloryczny: {dane_klienta['kalorie']} kcal
- Białko target: {dane_klienta['makro_target']['B']}g
- Tłuszcze target: {dane_klienta['makro_target']['T']}g
- Węglowodany target: {dane_klienta['makro_target']['W']}g
- Cel: {dane_klienta.get('cel', 'ogólny fitness')}
- Kontuzje/uwagi: {dane_klienta.get('kontuzje', 'brak')}

BAZA PRODUKTÓW — używaj WYŁĄCZNIE tych produktów (wartości na 100g):
{chr(10).join(products_lines)}

ZASADY KULINARNE — BEZWZGLĘDNIE PRZESTRZEGAJ:
1. Każdy posiłek ma JEDNO główne źródło białka (np. kurczak LUB jajka LUB twaróg — nie mieszaj kilku naraz)
2. Skyr/jogurt/twaróg NIE idzie razem z mięsem (kurczak, indyk, wołowina) w jednym posiłku
3. Śniadanie = jajka, owsianka, twaróg, skyr, kanapki z wędliną — wszystko co naturalnie je się rano
4. Obiad = mięso lub ryba + węglowodany (ryż, kasza, ziemniaki) + warzywa
5. Kolacja = lekkie białko (twaróg, jajka, ryba, wędlina) + warzywa
6. Orzechy/nasiona pasują do śniadań i przekąsek — nie do obiadu z mięsem
7. Każdy posiłek musi wyglądać jak realne, smaczne danie które można zjeść

WYMAGANY FORMAT ODPOWIEDZI — zwróć WYŁĄCZNIE czysty JSON (bez markdown, bez komentarzy):
{{
  "jadlospis": [
    {{
      "nazwa_posilku": "Posiłek 1: Śniadanie białkowo-tłuszczowe",
      "skladniki": [
        {{"Produkt": "dokładna nazwa z bazy", "Ilość": "150g"}},
        {{"Produkt": "dokładna nazwa z bazy", "Ilość": "100g"}}
      ],
      "notatki": "Krótka instrukcja przygotowania i wskazówki techniczne."
    }},
    {{
      "nazwa_posilku": "Posiłek 2: ...",
      "skladniki": [...],
      "notatki": "..."
    }}
  ]
}}"""

    print("\n   [AI] Generuję jadłospis — Gemini...\n")

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("   [BŁĄD] Brak klucza GEMINI_API_KEY w zmiennych środowiskowych.")
        print("          Pobierz darmowy klucz: aistudio.google.com → Get API key")
        return []

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        full_text = response.text
        print(full_text[:300] + "..." if len(full_text) > 300 else full_text)
    except Exception as e:
        print(f"   [BŁĄD] Gemini API: {e}")
        return []

    # Parsowanie JSON z odpowiedzi
    for attempt in [
        lambda t: json.loads(t.strip()),
        lambda t: json.loads(re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', t).group(1)),
        lambda t: json.loads(re.search(r'\{[\s\S]*\}', t).group(0)),
    ]:
        try:
            data = attempt(full_text)
            jadlospis = data.get("jadlospis", [])
            if jadlospis:
                print(f"\n   [OK] Jadłospis zawiera {len(jadlospis)} posiłki.")
                return jadlospis
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass

    print("   [!] Nie udało się sparsować JSON z odpowiedzi Gemini.")
    return []

# ══════════════════════════════════════════════════════════════════════════
# SEKCJA 3 — PLAN TRENINGOWY (logika z start_trening.py)
# ══════════════════════════════════════════════════════════════════════════

def get_smart_tempo(cw_name: str) -> str:
    n = cw_name.lower()
    if any(x in n for x in ["martwy ciąg", "przysiad", "wyciskanie"]):
        return "3-1-1-0"
    if any(x in n for x in ["wyprosty", "uginanie", "rozpiętki", "brama", "wznosy"]):
        return "2-0-1-2"
    if any(x in n for x in ["wiosłowanie", "ściąganie"]):
        return "3-0-1-1"
    return "3-0-1-0"


def pick_exercise(baza: list, used: set, muscle=None, type_f=None, gear_f=None, specific=None) -> dict:
    opts = [cw for cw in baza if cw["Nazwa_Cwiczenia"] not in used]
    if muscle:
        opts = [cw for cw in opts if muscle.lower() in cw["Partia_Glowna"].lower()]
    if type_f:
        opts = [cw for cw in opts if cw["Typ ćwiczenia"] == type_f]
    if gear_f:
        opts = [cw for cw in opts if cw["Sprzet"] in gear_f]
    if specific:
        opts = [cw for cw in opts if specific.lower() in cw["Nazwa_Cwiczenia"].lower()]

    if not opts:
        opts = [cw for cw in baza if cw["Nazwa_Cwiczenia"] not in used]
        if muscle:
            opts = [cw for cw in opts if muscle.lower() in cw["Partia_Glowna"].lower()]
    if not opts:
        opts = [cw for cw in baza if cw["Nazwa_Cwiczenia"] not in used]
    if not opts:
        opts = baza

    chosen = random.choice(opts)
    used.add(chosen["Nazwa_Cwiczenia"])
    return chosen


def build_session(name: str, base_structure: list, prio_mapped: list, baza: list, used: set) -> dict:
    prio_complex, prio_isol, other_complex, other_isol = [], [], [], []

    for item in base_structure:
        is_prio    = any(p.lower() in item["muscle"].lower() for p in prio_mapped)
        is_complex = item.get("type_f") == "Wielostawowe" or "specific" in item
        if is_prio:
            (prio_complex if is_complex else prio_isol).append(item)
        else:
            (other_complex if is_complex else other_isol).append(item)

    sesja = {"nazwa_sesji": name, "cwiczenia": []}
    for idx, item in enumerate(prio_complex + prio_isol + other_complex + other_isol):
        cw = pick_exercise(baza, used, muscle=item["muscle"],
                           type_f=item.get("type_f"), gear_f=item.get("gear_f"),
                           specific=item.get("specific"))

        is_prio = any(p.lower() in item["muscle"].lower() for p in prio_mapped)
        if is_prio:
            s = 4 if item.get("type_f") == "Wielostawowe" or idx == 0 else 3
        else:
            s = 3 if item.get("type_f") == "Wielostawowe" else 2

        sesja["cwiczenia"].append({
            "nazwa":       cw["Nazwa_Cwiczenia"],
            "serie":       s,
            "powtorzenia": "6-10" if cw["Typ ćwiczenia"] == "Wielostawowe" else "10-12",
            "notatki":     f"Tempo: {get_smart_tempo(cw['Nazwa_Cwiczenia'])}. {cw['Krótki opis techniki']}"
        })
    return sesja


def generuj_plan_treningowy(ankieta: dict) -> list:
    baza_path = os.path.join(BASE_DIR, "src", "baza_cwiczen_j.json")
    with open(baza_path, "r", encoding="utf-8") as f:
        baza = json.load(f)

    raw_dni = ankieta.get("dni", 3)
    try:
        dni = int(raw_dni)
        if not (2 <= dni <= 6):
            dni = 3
    except (TypeError, ValueError):
        dni = 3

    priorytety = ankieta.get("priorytet") or []
    map_prio = {
        "Klatka piersiowa": "Klatka", "Plecy": "Najszerszy",
        "Nogi": "Czworogłowy",        "Barki": "Naramienny",
        "Biceps": "Biceps",            "Triceps": "Triceps",
        "Pośladki": "Pośladki",       "Brzuch": "brzucha"
    }
    prio_mapped = [map_prio.get(p, p) for p in priorytety]
    used = set()
    plan = []

    if dni >= 4:
        p1 = [{"muscle": "Klatka",        "type_f": "Wielostawowe"},
              {"muscle": "Czworogłowy",    "type_f": "Wielostawowe"},
              {"muscle": "Naramienny (bok)","gear_f": ["Wyciąg"]},
              {"muscle": "Klatka",         "type_f": "Izolowane"},
              {"muscle": "Czworogłowy",    "type_f": "Izolowane"},
              {"muscle": "Triceps",         "gear_f": ["Wyciąg"]}]
        l1 = [{"muscle": "Najszerszy",     "specific": "ściąganie"},
              {"muscle": "Dwugłowy",       "type_f": "Wielostawowe"},
              {"muscle": "Najszerszy",     "specific": "wiosłowanie"},
              {"muscle": "Naramienny (tył)"},
              {"muscle": "Dwugłowy"},
              {"muscle": "Biceps",         "gear_f": ["Hantle"]}]
        p2 = [{"muscle": "Klatka",         "gear_f": ["Hantle"]},
              {"muscle": "Czworogłowy",    "specific": "Przysiad"},
              {"muscle": "Naramienny",     "gear_f": ["Sztanga", "Hantle"]},
              {"muscle": "Czworogłowy",    "specific": "bułgarskie"},
              {"muscle": "Klatka",         "gear_f": ["Wyciąg"]},
              {"muscle": "Triceps",        "gear_f": ["Hantle"]}]
        l2 = [{"muscle": "Najszerszy",     "gear_f": ["Drążek"]},
              {"muscle": "Dwugłowy",       "specific": "Dzień dobry"},
              {"muscle": "Najszerszy",     "gear_f": ["Hantle"]},
              {"muscle": "Naramienny (tył)"},
              {"muscle": "Biceps",         "gear_f": ["Sztanga"]},
              {"muscle": "brzucha"}]
        plan.append(build_session("PUSH 1 (Priorytety przód)", p1, prio_mapped, baza, used))
        plan.append(build_session("PULL 1 (Priorytety tył)",   l1, prio_mapped, baza, used))
        plan.append(build_session("PUSH 2 (Priorytety przód)", p2, prio_mapped, baza, used))
        plan.append(build_session("PULL 2 (Priorytety tył)",   l2, prio_mapped, baza, used))
    else:
        push  = [{"muscle": "Klatka",           "type_f": "Wielostawowe"},
                 {"muscle": "Naramienny",        "type_f": "Wielostawowe"},
                 {"muscle": "Klatka",            "type_f": "Izolowane"},
                 {"muscle": "Naramienny (bok)",  "type_f": "Izolowane"},
                 {"muscle": "Triceps",           "gear_f": ["Wyciąg"]},
                 {"muscle": "Triceps",           "gear_f": ["Hantle"]}]
        pull  = [{"muscle": "Najszerszy",        "specific": "ściąganie"},
                 {"muscle": "Najszerszy",        "specific": "wiosłowanie"},
                 {"muscle": "Naramienny (tył)"},
                 {"muscle": "Biceps",            "gear_f": ["Sztanga"]},
                 {"muscle": "Biceps",            "gear_f": ["Hantle"]},
                 {"muscle": "brzucha"}]
        legs  = [{"muscle": "Czworogłowy",       "type_f": "Wielostawowe"},
                 {"muscle": "Dwugłowy",          "type_f": "Wielostawowe"},
                 {"muscle": "Czworogłowy",       "type_f": "Izolowane"},
                 {"muscle": "Dwugłowy",          "type_f": "Izolowane"},
                 {"muscle": "łydki"},
                 {"muscle": "brzucha"}]
        plan.append(build_session("PUSH",  push, prio_mapped, baza, used))
        plan.append(build_session("PULL",  pull, prio_mapped, baza, used))
        plan.append(build_session("LEGS",  legs, prio_mapped, baza, used))

    return plan

# ══════════════════════════════════════════════════════════════════════════
# SEKCJA 4 — HTML PACKING (logika z pakuj_dieta.py + pakuj_trening.py)
# ══════════════════════════════════════════════════════════════════════════

def _get_weight(ilosc_str: str) -> float:
    match = re.search(r'(\d+)\s*g', str(ilosc_str).lower())
    return float(match.group(1)) if match else 0.0


def _normalize(name: str) -> str:
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'[^a-ząćęłńóśźż0-9\s]', ' ', name.lower())
    return ' '.join(name.split())


def find_product(name: str, db: list):
    nc = _normalize(name)
    normed = [(p, _normalize(p["Nazwa"])) for p in db]

    for p, pn in normed:
        if p["Nazwa"].lower().strip() == name.lower().strip():
            return p
    for p, pn in normed:
        if pn == nc:
            return p
    for p, pn in normed:
        if nc in pn or pn in nc:
            return p
    qw = set(nc.split())
    for p, pn in normed:
        if qw and qw.issubset(set(pn.split())):
            return p
    matches = difflib.get_close_matches(nc, [pn for _, pn in normed], n=1, cutoff=0.6)
    if matches:
        for p, pn in normed:
            if pn == matches[0]:
                return p
    return None


def generate_diet_html(jadlospis: list, produkty_db: list):
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
                b = round(pd["Bialko"]       * r, 1)
                t = round(pd["Tluszcz"]      * r, 1)
                w = round(pd["Weglowodany"]  * r, 1)
                k = round(pd["Kcal"]         * r, 0)
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

    return html, round(day_b, 1), round(day_t, 1), round(day_w, 1), round(day_kcal, 0)


def generate_summary_html(b, t, w, kcal, target: dict) -> str:
    k_b = b * 4; k_t = t * 9; k_w = w * 4
    total = k_b + k_t + k_w
    pct_b = round((k_b / total) * 100, 1) if total > 0 else 0
    pct_t = round((k_t / total) * 100, 1) if total > 0 else 0
    pct_w = round((k_w / total) * 100, 1) if total > 0 else 0
    diff_b = round(b - target.get("B", 0), 1)
    diff_t = round(t - target.get("T", 0), 1)
    diff_w = round(w - target.get("W", 0), 1)
    diff_k = round(kcal - target.get("kcal", 0), 1)

    return f'''
    <div class="table-container" style="margin-top:10px;border-top:2px solid #3b312b;padding-top:10px;">
        <div class="header" style="font-size:22px;">PODSUMOWANIE DNIA (REALNE)</div>
        <table>
            <thead><tr>
                <th style="width:25%">Białko (B)</th>
                <th style="width:25%">Tłuszcze (T)</th>
                <th style="width:25%">Węglowodany (W)</th>
                <th style="width:25%">Kalorie (Kcal)</th>
            </tr></thead>
            <tbody><tr style="font-size:18px;font-weight:600;">
                <td>{b} g</td><td>{t} g</td><td>{w} g</td><td>{kcal} kcal</td>
            </tr></tbody>
        </table>
        <div class="macro-bar-container">
            <div title="Białko"        style="width:{pct_b}%;background:#3498db;"></div>
            <div title="Tłuszcze"      style="width:{pct_t}%;background:#f1c40f;"></div>
            <div title="Węglowodany"   style="width:{pct_w}%;background:#e67e22;"></div>
        </div>
        <div class="macro-label-container">
            <span>🔵 Białko: {int(pct_b)}%</span>
            <span>🟡 Tłuszcze: {int(pct_t)}%</span>
            <span>🟠 Węglowodany: {int(pct_w)}%</span>
        </div>
        <!-- Cel: {target.get("B",0)}g B | {target.get("T",0)}g T | {target.get("W",0)}g W | {target.get("kcal",0)} kcal
             Różnica: {diff_b:+}g B | {diff_t:+}g T | {diff_w:+}g W | {diff_k:+} kcal -->
    </div>'''


def generate_training_html(plan_data: list) -> str:
    if not plan_data:
        return "<p>Brak danych treningowych.</p>"
    html = ""
    for session in plan_data:
        html += f'<div class="table-container">'
        html += f'  <div class="header">{session["nazwa_sesji"]}</div>'
        html += '  <table><thead><tr>'
        html += '    <th>Nazwa Ćwiczenia</th>'
        html += '    <th class="serie-col">Serie</th>'
        html += '    <th class="powt-col">Powtórzenia</th>'
        html += '  </tr></thead><tbody>'
        for cw in session["cwiczenia"]:
            html += ('      <tr><td>'
                     f'<span class="exercise-name">{cw["nazwa"]}</span>'
                     f'<span class="notes">{cw["notatki"]}</span>'
                     f'</td><td class="serie-col">{cw["serie"]}</td>'
                     f'<td class="powt-col">{cw["powtorzenia"]}</td></tr>')
        html += '  </tbody></table></div>'
    return html


def pack_dieta_html(dane_klienta: dict, produkty_db: list, output_dir: str) -> str:
    szablon = os.path.join(BASE_DIR, "master", "szablon_dieta_master.html")
    if not os.path.exists(szablon):
        print("   [!] Brak szablonu szablon_dieta_master.html")
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


def pack_trening_html(plan_trening: list, imie: str, output_dir: str) -> str:
    szablon = os.path.join(BASE_DIR, "master", "szablon_trening_master.html")
    if not os.path.exists(szablon):
        print("   [!] Brak szablonu szablon_trening_master.html")
        return ""

    with open(szablon, "r", encoding="utf-8") as f:
        html = f.read()

    html = html.replace("{{IMIE}}",   imie)
    html = html.replace("{{TRENING}}", generate_training_html(plan_trening))

    imie_safe = re.sub(r'[^\w\s-]', '', imie).strip().replace(' ', '_')
    out_path = os.path.join(output_dir, f"Plan_Treningowy_{imie_safe}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    return out_path

# ══════════════════════════════════════════════════════════════════════════
# SEKCJA 5 — GŁÓWNA LOGIKA
# ══════════════════════════════════════════════════════════════════════════

def wybierz_typ_planu() -> str:
    print("\n  Jaki plan chcesz wygenerować?")
    print("    1 — Tylko trening")
    print("    2 — Tylko dieta")
    print("    3 — Oba (trening + dieta)")
    while True:
        wyb = input("  Twój wybór [1/2/3]: ").strip()
        if wyb in ("1", "2", "3"):
            return wyb
        print("  [!] Wpisz 1, 2 lub 3.")


def utworz_folder_klienta(imie: str) -> str:
    imie_safe = re.sub(r'[^\w\s-]', '', imie).strip().replace(' ', '_')
    folder_name = f"{imie_safe}_{date.today().isoformat()}"
    output_dir = os.path.join(BASE_DIR, "klienci", folder_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def main():
    print("=" * 60)
    print("  PIPELINE KLIENTA — ONE CLICK")
    print("=" * 60)

    # ── Wczytaj plik ankiety ───────────────────────────────────────
    if len(sys.argv) < 2:
        print("\n  Użycie: python utworz_klienta.py <plik_ankiety.json>")
        print("  Przykład: python utworz_klienta.py Ankieta_Jan_Kowalski.json\n")
        sys.exit(1)

    ankieta_path = sys.argv[1]
    if not os.path.isabs(ankieta_path):
        ankieta_path = os.path.join(BASE_DIR, ankieta_path)

    if not os.path.exists(ankieta_path):
        print(f"\n  [BŁĄD] Plik nie istnieje: {ankieta_path}\n")
        sys.exit(1)

    with open(ankieta_path, "r", encoding="utf-8") as f:
        ankieta = json.load(f)

    imie = ankieta.get("imie", "Klient").strip()
    print(f"\n  Klient: {imie}")
    print(f"  Data:   {date.today().isoformat()}")

    # ── Wybór planu ────────────────────────────────────────────────
    typ = wybierz_typ_planu()
    robie_trening = typ in ("1", "3")
    robie_diete   = typ in ("2", "3")

    # ── Utwórz folder archiwum ────────────────────────────────────
    output_dir = utworz_folder_klienta(imie)
    print(f"\n  Folder klienta: {output_dir}")

    # Zapisz kopię ankiety
    ankieta_kopia = os.path.join(output_dir, "ankieta.json")
    with open(ankieta_kopia, "w", encoding="utf-8") as f:
        json.dump(ankieta, f, indent=2, ensure_ascii=False)

    # ── TRENING ────────────────────────────────────────────────────
    if robie_trening:
        print("\n" + "─" * 60)
        print("  [TRENING] Generuję plan treningowy...")
        print("─" * 60)

        plan_trening = generuj_plan_treningowy(ankieta)

        # Zapisz JSON
        trening_json = os.path.join(output_dir, "plan_treningowy.json")
        with open(trening_json, "w", encoding="utf-8") as f:
            json.dump(plan_trening, f, indent=2, ensure_ascii=False)
        print(f"  [OK] JSON: {trening_json}")

        # Pakuj HTML
        trening_html = pack_trening_html(plan_trening, imie, output_dir)
        if trening_html:
            print(f"  [OK] HTML: {trening_html}")

    # ── DIETA ──────────────────────────────────────────────────────
    if robie_diete:
        print("\n" + "─" * 60)
        print("  [DIETA] Obliczam makra i generuję jadłospis...")
        print("─" * 60)

        # Wczytaj bazę produktów
        produkty_path = os.path.join(BASE_DIR, "src", "produkty.json")
        with open(produkty_path, "r", encoding="utf-8") as f:
            produkty_db = json.load(f)

        # Oblicz makra
        dane_klienta = oblicz_makra(ankieta)
        print(f"\n  Wyniki obliczeń:")
        print(f"    Kalorie: {dane_klienta['kalorie']} kcal")
        print(f"    Białko:  {dane_klienta['makro_target']['B']}g")
        print(f"    Tłuszcze:{dane_klienta['makro_target']['T']}g")
        print(f"    Węgle:   {dane_klienta['makro_target']['W']}g")

        # Generuj jadłospis przez Claude
        jadlospis = generate_jadlospis(dane_klienta, produkty_db)
        dane_klienta["jadlospis"] = jadlospis

        # Zapisz JSON z danymi klienta
        dieta_json = os.path.join(output_dir, "dane_klienta.json")
        with open(dieta_json, "w", encoding="utf-8") as f:
            json.dump(dane_klienta, f, indent=2, ensure_ascii=False)
        print(f"  [OK] JSON: {dieta_json}")

        # Pakuj HTML
        dieta_html = pack_dieta_html(dane_klienta, produkty_db, output_dir)
        if dieta_html:
            print(f"  [OK] HTML: {dieta_html}")

    # ── PODSUMOWANIE ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  GOTOWE! Pliki zapisane w:")
    print(f"  {output_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
