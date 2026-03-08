# 📋 Instrukcja obsługi ankiety JSON (Automatyzacja)

Gdy otrzymasz od klienta plik JSON wygenerowany przez `Ankieta_Premium.html` (np. `Ankieta_Jan_Kowalski.json`), wykonaj poniższe kroki, aby wygenerować dietę i trening.

---

### Krok 1: Przygotowanie plików
System szuka danych w pliku o nazwie **`ankieta_j.json`**.
1. Skopiuj otrzymany plik JSON od klienta.
2. Wklej go do dwóch lokalizacji:
   - Folder: `ankieta_dieta/`
   - Folder: `ankieta_trening/`
3. **W obu folderach zmień nazwę wklejonego pliku na `ankieta_j.json`**.

### Krok 2: Generowanie Diety
1. Otwórz terminal w folderze `ankieta_dieta/`.
2. Uruchom skrypt poleceniem:
   ```powershell
   python start_dieta.py
   ```
3. **Wynik:** W folderze pojawi się plik `gotowe_dane_klienta.json` z obliczonymi kaloriami i makroskładnikami.

### Krok 3: Generowanie Planu Treningowego
1. Otwórz terminal w folderze `ankieta_trening/`.
2. Uruchom skrypt poleceniem:
   ```powershell
   python start_trening.py
   ```
3. **Wynik:** W folderze pojawi się plik `gotowy_plan_treningowy.json` z ćwiczeniami dopasowanymi do sprzętu i priorytetów klienta.

---

### ⚠️ Ważne uwagi:
- **Nazwa pliku:** Skrypty nie zadziałają, jeśli plik nie będzie nazywał się dokładnie `ankieta_j.json`.
- **Sprzęt:** Jeśli klient nie zaznaczy żadnego sprzętu w ankiecie, system domyślnie wybierze tylko ćwiczenia z masą własnego ciała.
- **Nadpisywanie:** Każde uruchomienie skryptu nadpisuje poprzednie wyniki (`gotowe_...json`). Jeśli chcesz zachować stare pliki, przenieś je do innego folderu.
