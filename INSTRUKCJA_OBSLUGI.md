# 📋 Instrukcja obsługi systemu CLI Fitness (Automatyzacja)

Poniżej znajduje się kompletna ścieżka postępowania: od otrzymania ankiety od klienta, aż po wygenerowanie gotowych, wizualnych planów treningowych i dietetycznych w formacie HTML.

---

### Krok 1: Przygotowanie plików (Ankieta)
System operuje na pliku o nazwie **`ankieta_j.json`**.
1. Skopiuj otrzymany od klienta plik JSON (wygenerowany przez `Ankieta_Premium.html`).
2. Wklej go do dwóch folderów:
   - `ankieta_dieta/`
   - `ankieta_trening/`
3. **W obu lokalizacjach zmień nazwę tego pliku na `ankieta_j.json`**.

---

### Krok 2: Generowanie danych obliczeniowych
Teraz musisz przetworzyć surową ankietę na konkretne wyliczenia kalorii oraz listę ćwiczeń.

1. **Dieta:**
   - Otwórz terminal w głównym folderze projektu.
   - Uruchom: `python ankieta_dieta/start_dieta.py`
   - **Wynik:** Powstanie plik `ankieta_dieta/gotowe_dane_klienta.json`.

2. **Trening:**
   - Uruchom: `python ankieta_trening/start_trening.py`
   - **Wynik:** Powstanie plik `ankieta_trening/gotowy_plan_treningowy.json`.

---

### Krok 3: Generowanie wizualnych plików HTML (Pakowanie)
To ostatni krok, który zamienia surowe dane JSON w eleganckie dokumenty dla klienta. Skrypty te znajdują się w folderze `master/`.

1. **Generowanie finalnego Treningu:**
   ```powershell
   python master/pakuj_trening.py
   ```
   - **Co się stanie:** Skrypt pobierze dane treningowe, imię klienta i wstawi je do profesjonalnego szablonu.

2. **Generowanie finalnej Diety:**
   ```powershell
   python master/pakuj_dieta.py
   ```
   - **Co się stanie:** Skrypt przeliczy makroskładniki każdego produktu z bazy `src/produkty.json` i wygeneruje przejrzysty jadłospis ze wskazówkami (nawodnienie, kofeina).

---

### Krok 4: Odbiór gotowych planów
Wszystkie wygenerowane pliki HTML trafiają automatycznie do folderu:
📂 **`plany/`**

Pliki będą nazwane według schematu:
- `Plan_Treningowy_Imię Nazwisko.html`
- `Plan_Dietetyczny_Imię Nazwisko.html`

---

### ⚠️ Ważne uwagi techniczne:
- **Spójność nazw:** Skrypty w `master/` szukają konkretnych plików: `ankieta_j.json`, `gotowe_dane_klienta.json` oraz `gotowy_plan_treningowy.json`. Nie zmieniaj ich nazw w trakcie procesu.
- **Baza produktów:** Jeśli w planie dietetycznym przy produkcie widzisz kreski (`-`) zamiast wartości, oznacza to, że nazwa produktu w jadłospisie nie została dopasowana do żadnej pozycji w `src/produkty.json`.
- **Nadpisywanie:** Każde ponowne uruchomienie skryptów nadpisuje pliki w folderze `plany/`. Jeśli robisz plany dla nowego klienta o tym samym imieniu, przenieś stare pliki do archiwum.
