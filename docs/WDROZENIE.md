# Wdrożenie: Supabase + Vercel + Przelewy24

Koszt infrastruktury wg biznesplanu: Vercel Pro 20 USD/mies., Supabase Pro od 25 USD/mies.
(darmowy plan Vercel Hobby nie jest do użytku komercyjnego).

## 1. Baza danych — Supabase

1. Utwórz projekt w regionie **Central EU (Frankfurt)** — dane gości zostają w UE.
2. *Project Settings → Database → Connection string*: skopiuj adres **Transaction pooler** (port 6543).
   To jest `DATABASE_URL` dla Vercel. Ustaw `DATABASE_SSL=require`.
3. Migracje uruchom z komputera adresem **Session pooler / direct** (port 5432):
   ```bash
   DATABASE_URL="postgres://…:5432/postgres" DATABASE_SSL=require npm run db:migrate
   ```
4. Supabase Pro robi codzienne kopie zapasowe (7 dni). Przed sylwestrem zrób dodatkowo ręczny zrzut.

System używa Supabase jako zarządzanego PostgreSQL. Logowanie managerów jest wbudowane (scrypt + sesje w bazie),
więc nie zależymy od Supabase Auth i bazę można w każdej chwili przenieść do innego dostawcy Postgresa.

## 2. Aplikacja — Vercel

1. Importuj repozytorium w Vercel (framework: Next.js). Region funkcji ustawia `vercel.json` (`fra1`).
2. Zmienne środowiskowe (Production):

| Zmienna | Wartość |
|---|---|
| `DATABASE_URL` | adres Transaction pooler z Supabase |
| `DATABASE_SSL` | `require` |
| `DB_POOL_MAX` | `3` |
| `APP_URL` | `https://twoja-domena.pl` |
| `APP_SECRET` | losowe 32+ znaki: `node -e "console.log(require('crypto').randomBytes(32).toString('base64url'))"` — **nie zmieniaj po starcie** (szyfruje dane P24 klubów) |
| `ALLOW_MOCK_PAYMENTS` | `false` |
| `RESEND_API_KEY`, `MAIL_FROM` | e-maile z biletami (domena zweryfikowana w Resend) |
| `CRON_SECRET` | losowy ciąg — Vercel wysyła go do raportu porannego |
| `CUSTOM_DOMAINS` | np. `bilety.klubx.pl=klubx` (domenę dodaj też w Vercel → Domains) |

3. Raport poranny: `vercel.json` uruchamia `/api/cron/raport-poranny` o 4:00 UTC (6:00 czasu letniego, 5:00 zimowego).
4. Monitoring: podepnij `GET /api/health` pod darmowy monitor (np. UptimeRobot) z alertem SMS na piątek–sobota.

Środowisko testowe: osobny projekt Vercel (Preview) + osobna baza, `ALLOW_MOCK_PAYMENTS=true`.

## 3. Płatności — Przelewy24 (konto klubu)

1. Klub zakłada konto firmowe w Przelewy24 (weryfikacja: od kilku godzin do kilku dni) — najlepiej zaraz po nocy testowej.
2. W panelu P24 klub odczytuje: **ID sprzedawcy**, **ID sklepu**, **klucz CRC**, **klucz do raportów (API)**.
3. Manager wpisuje je w *Panel → Ustawienia → Płatności online*. Na start zaznacz „tryb testowy (sandbox)”
   i wykonaj zakup testowy; potem odznacz.
4. Adres powiadomień: `https://twoja-domena.pl/api/platnosci/p24` (system podaje go automatycznie przy każdej transakcji).
5. Przed startem: wynegocjuj stawki (cennik standardowy 1,29% + 0,30 zł) i potwierdź u doradcy podatkowego
   kwestie kasy fiskalnej i VAT przy sprzedaży online (rozdział „Prawo i regulacje”).

## 4. Lista kontrolna przed pierwszymi prawdziwymi pieniędzmi

- [ ] Przegląd kodu i bezpieczeństwa przez doświadczonego programistę (budżet 2–5 tys. zł).
- [ ] Regulamin i polityka prywatności sprawdzone przez prawnika (`/regulamin`, `/prywatnosc` to projekty).
- [ ] Umowa powierzenia danych z klubem.
- [ ] `ALLOW_MOCK_PAYMENTS=false` w produkcji.
- [ ] Test zakupu w sandboxie P24 i jednego prawdziwego zakupu za 1 zł z natychmiastowym zwrotem.
- [ ] Próba „awarii w sobotę”: telefony w trybie samolotowym, lista do druku, przywrócenie sieci.
