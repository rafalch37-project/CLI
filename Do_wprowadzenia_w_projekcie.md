# Do wprowadzenia w projekcie

Poniżej znajduje się lista propozycji narzędzi i skryptów do wdrożenia, uszeregowana według priorytetów jako rozszerzenie obecnego systemu (bazy ćwiczeń, szablonów, ankiet i dzienników):

### 1. Generator Zautomatyzowanej Listy Zakupów 🛒
*   **Cel:** Na podstawie planów dietetycznych i bazy `produkty.json` automatycznie wygenerować zsumowaną listę składników (np. na 7 dni).
*   **Podział:** Warzywa, Mięso, Nabiał itp.
*   **Działanie:** Narzędzie odczytuje gotowy jadłospis klienta, robi błyskawiczną matematykę i tworzy listę do wysłania klientowi razem z dietą. Oszczędność czasu dla trenera i ogromny plus dla wygody podopiecznego.

### 2. Edytor „Zamienników Produktów” 🔄
*   **Cel:** Zautomatyzowane wyliczanie alternatywnych produktów na podstawie zadanej porcji makroskładników.
*   **Działanie:** Jeśli np. klient potrzebuje zastąpić 100g piersi z kurczaka, program sięga do bazy `produkty.json` i podaje precyzyjną gramaturę 2-3 odpowiedników (twaróg, łosoś, wołowina). Dokument można załączyć na koniec planu dietetycznego. Zapobiega to setkom powtarzających się pytań poprzez SMS.

### 3. Moduł „Lifestyle & Suplementacja” 💊😴
*   **Cel:** Zwiększenie świadomości klienta bez ręcznego wypisywania rad za każdym razem. Tworzymy `system_prompt_suple.md`.
*   **Zawartość:** Wytyczne dotyczące snu jako filaru regeneracji do treningu 3-1-1-0. Baza protokołów suplementacji dla różnych celów (redukcja, masa: dawkowanie kreatyny, kofeiny, omega-3). Prosty generator podsumowujący dzienny NEAT i regenerację.

### 4. Skrypt Centralny (Narzędzie "One-Click / Orchestrator") ⚙️
*   **Cel:** Skrypt w Pythonie (np. `utworz_klienta.py`), który zbiera ankietę (`ankieta.xlsx`) i systemowe zasady (Trening / Dieta), a potem od razu generuje strukturę katalogu klienta.
*   **Działanie:** Oszczędność klikania - od razu kopiuje materiały szkoleniowe (`Fitatu.md`, nowatorską obsługę platformy), wymusza połączenie AI z promptem i kreuje zarysy plików dla trenera do ostatecznej korekty.

### 5. Kalkulator Ciężaru Dźwiganego / Progresji (Makrocykle) 🏋️‍♂️
*   **Cel:** Przypisanie konkretnych cyfr do planów. Skrypt lub plik HTML.
*   **Działanie:** Trener podaje parametry (np. szacunkowy Max klienta w przysiadzie). Skrypt przypisuje obciążenie dla wszystkich ciężkich serii głównych na cały 4-tygodniowy mikrocykl wedle skali RPE. Pomaga uniknąć błąkającego się we mgle klienta.

### 6. Gotowe Szablony "Follow-up" i Szablon Check-In ✅
*   **Cel:** Standaryzacja i odciążenie pamięci krótkotrwałej przy komunikacji z leniwymi na swój sposób klientami - `szablony_maili.md`.
*   **Działanie:** Zawiera zarysy wiadomości wycelowanych w poszczególne dni m.in. na start (po wysłaniu planów), przypomnienie na 2 dni przed raportowaniem (Check-in), oraz standardowy komunikat sprzedażowy pod koniec wariantu opieki (by zachęcić do powrotu lub polecenia kogoś).
*   **STATUS: DO ZROBIENIA** — gotowe szablony SMS/WhatsApp na: dzień 1 po wysłaniu planów, 2 dni przed check-inem, koniec pakietu.

---

## Do zaimplementowania (priorytety)

### A. Skrypt Centralny "One-Click" ⚙️ — PRIORYTET
*   **Co to:** Jeden skrypt Python który odpala całość pipeline'u automatycznie.
*   **Flow:** Klient wypełnia ankietę → `start_dieta.py` liczy kalorie/makra → Claude API generuje jadłospis → gotowy plik JSON zapisany.
*   **Teraz:** Robisz to w kilku krokach ręcznie — skrypt to połączy w jedno kliknięcie.
*   **Plik docelowy:** `utworz_klienta.py`

### B. Szablony Follow-up ✅ — PROSTE DO ZROBIENIA
*   **Co to:** Gotowe wiadomości SMS/WhatsApp do kopiuj-wklej dla klientów.
*   **Kiedy wysyłać:** Po wysłaniu planów (dzień 1), 2 dni przed check-inem, koniec pakietu (oferta przedłużenia).
*   **Plik docelowy:** `szablony_komunikacji.md`
