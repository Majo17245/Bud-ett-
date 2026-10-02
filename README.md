# Klubowy — system dla klubów (wersja wstępna)

**Cały klub w jednym systemie — od DM do bramki.** Bilety z pulami cenowymi, loże z przedpłatą na mapie sali,
listy gości z limitem i godziną wejścia, promotorzy z automatycznymi prowizjami, skaner bramki działający
bez internetu i raport na żywo. Zakres i liczby pochodzą z dokumentu
„System dla klubów – analiza rynku i biznesplan” (zakładki: funkcje produktu, cennik, plan ekspresowy).

> W repozytorium jest też niezależny plik `budzet-standalone.html` (osobna aplikacja budżetowa) — system go nie używa.

## Co już działa

| Moduł | Funkcja | Etap w biznesplanie |
|---|---|---|
| Sprzedaż | strona klubu z kalendarzem imprez PL/EN, dane strukturalne dla Google | MVP |
| Sprzedaż | pule cenowe z automatycznym skokiem (early bird → I pula → II pula), limity, bilety grupowe, kody rabatowe | MVP |
| Sprzedaż | płatności przez Przelewy24 (BLIK, karty) na konto klubu + symulator płatności do testów | MVP |
| Sprzedaż | zakup bez konta, opłata serwisowa 5% (min. 1,49 zł) lub wg planu, płaci kupujący albo klub | MVP |
| Loże | mapa sali, cena za osoby, dopłata za dodatkowe osoby, przedpłata %, blokada podwójnej rezerwacji | MVP |
| Loże | prośba o rezerwację (bez płatności — noc testowa) i rezerwacje z telefonu/DM w panelu | v0 |
| Listy | listy z limitem osób i godziną wejścia, osoby towarzyszące, blokada duplikatów między listami | MVP |
| Listy | zaproszenia z kodem QR | v0 |
| Promotorzy | kody i linki, własne listy, panel promotora bez hasła, ranking, wyliczona prowizja | MVP |
| Bramka | skaner PWA na każdy telefon, tryb offline, wiele telefonów naraz, licznik osób w sali | MVP |
| Bramka | import kodów z RA / Going / Biletomatu / eBilet do jednej bramki | Faza 2 |
| Bramka | lista do druku jako plan B | v0 |
| Goście | baza gości ze zgodami marketingowymi, eksport CSV, usuwanie danych (RODO) | MVP |
| Zarządzanie | raport na żywo (wejścia, kanały, pule, listy, loże, promotorzy), raport poranny e-mailem | MVP |

Nie ma jeszcze (zgodnie z planem — faza 2 i 3): mObywatel, asystent DM z AI, KSeF, SMS-y, płatności odroczone,
karnety, POS, cashless, wiele lokali w jednym panelu, automatyczne wypłaty prowizji.

## Szybki start (lokalnie)

Wymagania: Node.js 20+, PostgreSQL 14+.

```bash
npm install
cp .env.example .env.local           # uzupełnij DATABASE_URL i APP_SECRET
set -a && . ./.env.local && set +a
npm run db:migrate                   # schemat bazy
npm run db:seed                      # klub demo, impreza, loże, 3 promotorów, 300 zaproszeń
npm run dev                          # http://localhost:3000
```

Seed wypisze linki: panel (`demo@klubowy.local` / `demo-haslo-123`), stronę klubu, skaner bramki i panel promotora.

## Testy

```bash
TEST_DATABASE_URL=postgres://app:app@localhost:5432/klub_test npm test
```

Testy działają na prawdziwym PostgreSQL (baza testowa jest czyszczona przy każdym uruchomieniu) i sprawdzają m.in.:
brak sprzedaży ponad pulę przy równoległych zakupach, idempotentne powiadomienia o płatności, pule cenowe,
duplikaty na listach, podwójne rezerwacje loż, synchronizację dwóch telefonów bramki po pracy offline i prowizje promotorów.

## Dokumentacja

- [docs/ARCHITEKTURA.md](docs/ARCHITEKTURA.md) — jak to jest zbudowane i dlaczego
- [docs/WDROZENIE.md](docs/WDROZENIE.md) — Supabase + Vercel + Przelewy24 krok po kroku
- [docs/NOC-TESTOWA.md](docs/NOC-TESTOWA.md) — scenariusz testu na sucho i pierwszej nocy w klubie
