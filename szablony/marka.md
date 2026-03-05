# Księga Stylu (Brandbook) - Twoja Marka

Ten dokument zawiera wszystkie parametry wizualne używane w projektach planów treningowych, dietetycznych i arkuszy postępów.

## 1. Kolorystyka
- **Złoty (Główny/Tekst nagłówków):** `#d4af37` (Używany w `th` i `.card-title`)
- **Ciemny Brąz (Tło nagłówków/Akcenty):** `#3b312b` (Główny kolor identyfikacji)
- **Złoty Przygaszony (Obramowania/Linie):** `#c5a059` (Używany w ramkach tabel i polach wejściowych)
- **Tekst Główny:** `#333333`
- **Tło Kart:** `rgba(255, 255, 255, 0.6)` (Półprzezroczysta biel, aby logo pod spodem było widoczne)

## 2. Typografia
- **Czcionka główna:** `Montserrat` (Google Fonts)
- **Nagłówki sekcji:** `letter-spacing: 5px-6px`, `text-transform: uppercase`, `font-weight: 600`
- **Tekst standardowy:** `font-size: 13px - 14px`, `line-height: 1.6`

## 3. Elementy Graficzne
- **Watermark (Logo w tle):** 
  - Pozycja: `fixed` (na środku ekranu)
  - Przezroczystość (Opacity): `0.12` do `0.15`
  - Szerokość: `110%` (lekko wystające poza krawędzie dla efektu nowoczesności)
- **Karty sekcji:** `border-left: 4px solid #3b312b` (charakterystyczna pionowa linia po lewej stronie)

## 4. Ustawienia Druku (PDF)
- **Format:** A4
- **Marginesy:** Brak (0) w definicji `@page`, ale padding `15mm - 20mm` wewnątrz body.
- **Wymóg:** `-webkit-print-color-adjust: exact;` (aby kolory tła drukowały się poprawnie)
