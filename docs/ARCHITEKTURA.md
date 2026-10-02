# Architektura

Zgodnie z biznesplanem: proste technologie, mało ruchomych części, dane w UE, koszty infrastruktury ok. 50 USD/mies.

```
 Gość (telefon)            Manager / promotor            Ochrona (telefon, PWA)
      │                           │                              │
      ▼                           ▼                              ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │  Next.js 16 na Vercel (region fra1)                                    │
 │  • /k/[klub]/e/[impreza]  strona imprezy, zakup, mapa loż (PL/EN)      │
 │  • /panel/...             panel klubu (server actions)                 │
 │  • /promotor/[token]      panel promotora (link bez hasła)             │
 │  • /bramka/[impreza]      skaner offline: service worker + IndexedDB   │
 │  • /api/door/*            manifest kodów i synchronizacja skanów       │
 │  • /api/platnosci/p24     powiadomienia Przelewy24                     │
 │  • /api/cron/raport-poranny  podsumowanie nocy e-mailem (Vercel Cron)  │
 └───────────────┬────────────────────────────┬───────────────────────────┘
                 │ SQL (pg, pooler)           │ REST
                 ▼                            ▼
     PostgreSQL (Supabase, Frankfurt)   Przelewy24 — konto KLUBU (pieniądze od razu u klubu)
                                        Resend — e-maile z biletami
```

## Najważniejsze decyzje

**Pieniądze nigdy nie przechodzą przez nasze konto.** Każdy klub ma własne konto w Przelewy24; system rejestruje
transakcję w imieniu klubu (dane dostępowe zaszyfrowane AES-256-GCM kluczem z `APP_SECRET`). To omija ryzyko
licencji KNF na usługi płatnicze i daje klubowi płynność. Naszą opłatę w pilotażu fakturujemy klubowi raz w miesiącu;
później można przejść na Przelewy24 Marketplace / Tpay z podziałem środków (wtedy opłata pobiera się sama).

**Sprzedaż bez overbookingu.** Zamówienie blokuje wiersze pul (`SELECT … FOR UPDATE`) i liczy wolne miejsca
z opłaconych zamówień oraz tych w trakcie płatności (15 minut). Test `równoległe zamówienia nie sprzedadzą więcej
niż jest w puli` odpala 8 równoległych zakupów na 5 biletów.

**Powiadomienia o płatności są idempotentne.** `finalizeOrder` blokuje zamówienie i wydaje bilety tylko raz —
P24 może ponawiać powiadomienie dowolnie wiele razy.

**Bramka działa bez internetu.** Telefon pobiera manifest (wszystkie kody: bilety, listy, loże, kody z innych
platform) do IndexedDB i sprawdza kody lokalnie. Każdy skan dostaje `clientId`, trafia do kolejki i wysyła się
paczkami, gdy wróci zasięg (`door_events` z unikalnym `(event_id, client_id)` — ponowna wysyłka nic nie psuje).
Serwer wydaje ostateczny werdykt: jeśli dwa telefony offline wpuściły ten sam kod, drugi skan dostaje „duplicate”,
a telefon pokazuje to w historii. Telefony co kilka sekund pobierają kody wpuszczone przez inne urządzenia.
Service worker trzyma powłokę skanera, więc strona otwiera się nawet bez sieci (po pierwszym otwarciu z internetem).

**Ochrona nie zakłada kont.** Manager generuje link (token w części `#` adresu — nie trafia do logów serwera),
pokazuje go jako kod QR, telefon bramki zapisuje token lokalnie. Token wygasa 12 h po końcu imprezy
i można go wyłączyć w panelu. Promotorzy dostają analogiczny link do swojego panelu.

**Kody wejścia** to 12 znaków alfabetu Crockforda (bez I/L/O/U — łatwo przeczytać na głos), prefiks T/G/L
(bilet/gość/loża), 55 bitów losowości. Kody z innych platform trzymamy w `external_tickets` w oryginalnej postaci.

**Duplikaty na listach** wykrywa klucz nazwiska bez polskich znaków, wielkości liter i kolejności członów
(„Kowalski Jan” = „jan kowalski”) oraz numer telefonu w formacie E.164. Dopisywanie blokuje imprezę na czas
transakcji, więc dwie listy dopisywane równolegle nie przepuszczą tej samej osoby.

**RODO.** Brak zdjęć i kopii dokumentów; zgoda marketingowa osobno i tylko „włącza się”; anonimizacja gościa
w panelu; eksport CSV tylko osób ze zgodą (z ochroną przed wstrzyknięciem formuł). Sekrety jednorazowe (link
promotora, hasło tymczasowe) są pokazywane przez krótkotrwałe ciasteczko, a nie w adresie URL.

**Promocje bez kryterium płci.** System nie ma „wejścia dla pań”; zamiast tego kody rabatowe, listy z godziną
wejścia i pule early bird (zob. „Równe traktowanie” w biznesplanie).

## Model danych (skrót)

`orgs` (klub/organizator, plan, kto płaci opłatę, operator płatności) → `events` → `ticket_types` (pule) →
`orders` / `order_items` → `tickets`. Obok: `guest_lists` → `guest_entries`, `lounges` → `lounge_reservations`,
`promoters`, `discount_codes`, `external_tickets`, `guests` (CRM), `door_tokens`, `door_events` (dziennik bramki).
Kwoty zawsze w groszach (`int`), czas w `timestamptz`, strefa klubu `Europe/Warsaw`.

## Struktura kodu

```
db/migrations/        SQL (stosowany przez scripts/migrate.ts)
scripts/              migracje i dane demo
src/lib/              logika niezależna od UI (testowana): pricing, crypto, payments, services/*
src/app/              strony i API (Next.js App Router, server actions)
public/sw.js          service worker skanera
tests/                testy na prawdziwym PostgreSQL
```

## Co dalej (kolejność z biznesplanu)

1. Przegląd kodu przez doświadczonego programistę przed pierwszymi prawdziwymi pieniędzmi.
2. Faza 2: SMS (SMSAPI), automatyczne wypłaty prowizji, mObywatel (środowisko testowe od 16.09.2026),
   asystent rezerwacji w DM, KSeF, płatności odroczone, karnety, sprzedaż promotora z telefonu.
3. Faza 3: wiele lokali w jednym panelu, POS, prognoza frekwencji i grafiku, cashless.
