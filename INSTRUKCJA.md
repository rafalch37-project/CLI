# Instrukcja obsługi — CLI Fitness Pipeline

## Wymagania wstępne

### 1. Instalacja bibliotek Python
```bash
pip install google-genai
```

### 2. Ustawienie klucza API Gemini
1. Wejdź na https://aistudio.google.com/
2. Utwórz nowy klucz API
3. Ustaw zmienną środowiskową:

**Windows (PowerShell) — tymczasowo:**
```powershell
$env:GEMINI_API_KEY = "twoj_klucz_tutaj"
```

**Windows — na stałe (zalecane):**
- Panel sterowania → System → Zmienne środowiskowe
- Nowa zmienna użytkownika: `GEMINI_API_KEY` = `twoj_klucz`
- Restartuj terminal po ustawieniu

---

## Struktura folderów

```
CLI/
├── klienci/                    ← tutaj trafiają gotowe plany klientów
│   └── Imie_Nazwisko_Data/
│       ├── dane_klienta.json
│       ├── Plan_Dietetyczny_Imie.html
│       └── Plan_Treningowy_Imie.html
├── ankieta_dieta/
│   └── ankieta_j.json          ← ankieta diety do wypełnienia
├── ankieta_trening/
│   └── ankieta_j.json          ← ankieta treningu do wypełnienia
├── src/
│   ├── produkty.json
│   ├── baza_cwiczen_j.json
│   ├── system_prompt_diet.md
│   └── system_prompt_trening.md
├── master/
│   ├── szablon_dieta_master.html
│   └── szablon_trening_master.html
├── utworz_klienta.py           ← GŁÓWNY SKRYPT
└── popraw_diete.py             ← korekta jadłospisu
```

---

## Krok 1 — Wypełnienie ankiety

Klient wypełnia `Ankieta_Premium.html` i odsyła plik JSON.

Umieść otrzymany plik JSON w odpowiednim folderze:
- **Dieta:** `ankieta_dieta/ankieta_j.json`
- **Trening:** `ankieta_trening/ankieta_j.json`

---

## Krok 2 — Generowanie planu

Uruchom skrypt główny:

```bash
# Tylko dieta:
python utworz_klienta.py ankieta_dieta\ankieta_j.json

# Tylko trening:
python utworz_klienta.py ankieta_trening\ankieta_j.json

# Oba plany naraz:
python utworz_klienta.py ankieta_dieta\ankieta_j.json ankieta_trening\ankieta_j.json
```

Skrypt automatycznie:
1. Wczytuje dane z ankiety
2. Oblicza BMR, TDEE i makroskładniki (Mifflin-St Jeor)
3. Generuje jadłospis przez Gemini AI
4. Generuje plan treningowy (push/pull/legs)
5. Tworzy folder `klienci/Imie_Nazwisko_Data/`
6. Zapisuje `dane_klienta.json`
7. Pakuje gotowe pliki HTML

Gotowe pliki HTML znajdziesz w: `klienci/Imie_Nazwisko_Data/`

---

## Krok 3 — Korekta jadłospisu (opcjonalnie)

Jeśli coś wymaga zmiany w jadłospisie, użyj `popraw_diete.py` — **bez generowania od nowa**.

```bash
python popraw_diete.py "Imie_Nazwisko_Data" "opis zmian"
```

### Przykłady:
```bash
python popraw_diete.py "Beata_Chmielowska_2026-03-22" "zamien kurczaka w posilku 2 na lososia"

python popraw_diete.py "Beata_Chmielowska_2026-03-22" "usun skyr z posilku 3, zastap twarogiem"

python popraw_diete.py "Beata_Chmielowska_2026-03-22" "zmien sniadanie na owsianke z bananem"
```

Skrypt:
1. Wysyła aktualny jadłospis + opis zmian do Gemini
2. Nanosi TYLKO opisane zmiany (reszta bez zmian)
3. Aktualizuje `dane_klienta.json`
4. Przepakowuje HTML

---

## Lista dostępnych klientów

Aby zobaczyć wszystkich klientów w archiwum:
```bash
ls klienci\
```

Lub uruchom `popraw_diete.py` bez argumentów — wyświetli listę:
```bash
python popraw_diete.py
```

---

## Rozwiązywanie problemów

### Brak klucza API
```
[BLAD] Brak klucza GEMINI_API_KEY.
```
Ustaw zmienną środowiskową — patrz sekcja "Wymagania wstępne".

### Błąd 429 (przekroczony limit)
```
BLAD: 429 RESOURCE_EXHAUSTED
```
- Darmowy limit: ~1500 zapytań/dzień
- Poczekaj chwilę i spróbuj ponownie
- Sprawdź czy klucz jest z projektu z włączonym darmowym tierem (aistudio.google.com)

### Pusty jadłospis po generowaniu
Sprawdź czy Gemini odpowiada poprawnie:
```bash
python test_gemini.py
```

### Klient nie pojawia się w folderze klienci/
Skrypt tworzy folder tylko po pomyślnym wygenerowaniu danych. Sprawdź komunikaty błędów w terminalu.
