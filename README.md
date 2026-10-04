# Bybit USDT-Perpetual Trading Bot (BTCUSDT, ETHUSDT, BTC/ETH)

Kompletny algorytm handlowy w Pythonie dla Bybit (API V5, kategoria `linear`):
analiza wieloczasowa (1d / 4h / 1h), scoring z siedmiu modułów, twarde zasady
ryzyka, egzekucja ze stop lossem ustawianym na giełdzie razem z otwarciem,
backtest z walk-forward, powiadomienia Telegram i dashboard Streamlit.

> **Domyślnie bot działa na Bybit Testnet.** Handel prawdziwymi środkami włącza
> się wyłącznie w `config/config.yaml`: `mode: live` **oraz** `live_confirm: true`.
> Żaden algorytm nie gwarantuje zysku. Zanim uruchomisz go na prawdziwym koncie,
> zrób backtest na danych z Bybit (sekcja 4) i co najmniej kilka tygodni testów na testnecie.

---

## 1. Struktura projektu

```
config/      config.yaml (WSZYSTKIE parametry), macro_events.yaml, settings.py (twarde limity)
data/        bybit_client.py (REST V5), bybit_ws.py (websocket: orderbook, publicTrade, allLiquidation, tickers),
             cross_exchange.py (Binance/OKX/Coinbase/Kraken przez CCXT), coinglass.py, macro.py (yfinance),
             sentiment.py (Fear & Greed), econ_calendar.py (dane makro USA), history.py (dane do backtestu),
             synthetic.py (dane syntetyczne - tylko testy techniczne)
indicators/  trend.py (EMA, ADX, HH/HL/LH/LL, BOS), momentum.py (RSI, MACD, dywergencje), volatility.py (ATR),
             volume.py (CVD, RVOL, Volume Profile), liquidations.py (model klastrów likwidacji),
             positioning.py (OI, funding, long/short), orderbook.py (imbalance, ściany, spoofing),
             macro.py (korelacje, risk-on/off), sentiment.py
signals/     features.py (cechy 1h/4h/1d bez lookahead), scoring.py, engine.py (reguły wejścia/wyjścia),
             levels.py (SL/TP)
risk/        sizing.py (wielkość pozycji, dźwignia), manager.py (limity portfela)
execution/   bybit_exec.py (zlecenia), position_manager.py (zarządzanie, przejmowanie po restarcie),
             live.py (pętla bota), state.py, testnet_check.py
backtest/    engine.py, metrics.py, walkforward.py, run.py, reports/
notifications/telegram.py
dashboard/app.py
logs/        bot.log, decisions.jsonl (każda decyzja z wartościami wskaźników), trades.jsonl, state.json
tests/       testy jednostkowe (ryzyko, backtest, egzekucja na atrapie Bybit V5)
bot.py       punkt wejścia bota
```

---

## 2. Instrukcja uruchomienia krok po kroku

### 2.1. Instalacja
```bash
git clone <repo> && cd <repo>
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # uzupełnisz w kroku 2.3
pytest                             # wszystkie testy powinny przejść
```

### 2.2. Konto na Bybit Testnet
1. Wejdź na **https://testnet.bybit.com** i kliknij **Sign Up**. Testnet to osobny system:
   konto zakładasz od nowa (może być ten sam e-mail co na bybit.com).
2. Po zalogowaniu przejdź do **Assets**. Pobierz testowe środki przyciskiem do zasilenia konta
   testowymi monetami (np. *Request Test Coins* / *Faucet*) i wybierz **USDT**.
3. Konto testnet jest domyślnie kontem **Unified Trading (UTA)**. Jeśli masz konto klasyczne,
   ustaw w `config.yaml` `exchange.account_type: CONTRACT`.

### 2.3. Klucze API (testnet)
1. Na testnet.bybit.com: ikona profilu → **API** → **Create New Key** → **System-generated API Keys**.
2. Uprawnienia: **Read-Write**, zaznacz wyłącznie **Contract → Orders** i **Positions**
   (w UTA: *Unified Trading → Orders, Positions*).
   **Nie zaznaczaj** niczego w sekcjach *Withdrawal*, *Transfer*, *Assets*/*Wallet*.
3. **IP restriction:** wybierz *Only IPs with permissions granted…* i wpisz swój publiczny adres IP
   (sprawdzisz go np. na https://ifconfig.me). Klucz bez ograniczenia IP Bybit i tak unieważnia po 3 miesiącach.
4. Wklej klucz i sekret do `.env`:
   ```
   BYBIT_TESTNET_API_KEY=...
   BYBIT_TESTNET_API_SECRET=...
   ```

> **Bezpieczeństwo:** klucz ma mieć uprawnienia **tylko do handlu, bez wypłat**, najlepiej
> z ograniczeniem do Twojego IP. Nigdy nie commituj pliku `.env` (jest w `.gitignore`).
> Do konta live wygeneruj osobny klucz na bybit.com z tymi samymi ograniczeniami.

### 2.4. Test połączenia i zleceń na testnecie
```bash
python -m execution.testnet_check          # BTCUSDT: market z stopLoss+takeProfit, weryfikacja, zamknięcie
python -m execution.testnet_check --pair   # dodatkowo dwie nogi pary BTC/ETH z SL
```
Skrypt sprawdza: połączenie (czas serwera), saldo (czyli czy klucze działają), tryb one-way
i margin isolated, złożenie zlecenia market **z parametrami `stopLoss` i `takeProfit`**, obecność SL/TP
na pozycji, cenę likwidacji za SL, częściowy TP (limit reduce-only), przesunięcie SL (`set_trading_stop`),
a na końcu anuluje zlecenia i zamyka pozycję. Wypisuje listę `[OK]` / `[BŁĄD]`. Jeśli na koncie jest już
otwarta pozycja BTC/ETH, test przerywa się, żeby jej nie naruszyć.

### 2.5. Backtest na danych z Bybit
```bash
python -m data.history --years 2.5     # pobiera świece 1h/4h/1d, funding, OI, long/short, US500, złoto, F&G
python -m backtest.run                  # pełny okres + hold-out OOS + walk-forward -> backtest/reports/<data>_bybit/
# lub w jednym kroku:  python -m backtest.run --source bybit
```
Raport (`report.md`, CSV transakcji i equity, JSON metryk) zawiera: zwrot, CAGR, max drawdown,
win rate, średnie R:R (planowane i zrealizowane), profit factor, Sharpe, Sortino, liczbę transakcji,
podział na long/short i na każdy instrument (BTCUSDT, ETHUSDT, BTC/ETH).
`python -m backtest.run --source synthetic` uruchamia ten sam pipeline na danych syntetycznych
(tylko test techniczny, bez wartości prognostycznej).

### 2.6. Uruchomienie bota
```bash
python bot.py --once      # jeden cykl analizy (sprawdzenie, czy wszystko działa)
python bot.py             # praca ciągła (Ctrl+C zatrzymuje)
streamlit run dashboard/app.py   # dashboard: http://localhost:8501
```
Bot co 10 s synchronizuje pozycje z giełdą, a 8 s po zamknięciu każdej świecy 1h robi pełną analizę.
Każda decyzja (wejście lub brak wejścia, z powodami i wartościami wszystkich wskaźników) trafia do
`logs/decisions.jsonl`, transakcje do `logs/trades.jsonl`, log techniczny do `logs/bot.log`.

### 2.7. Telegram (opcjonalnie)
1. W Telegramie napisz do **@BotFather** → `/newbot` → skopiuj token do `TELEGRAM_BOT_TOKEN`.
2. Napisz cokolwiek do swojego bota, otwórz `https://api.telegram.org/bot<TOKEN>/getUpdates`
   i skopiuj `chat.id` do `TELEGRAM_CHAT_ID`.
Bot wysyła powiadomienia o otwarciu i zamknięciu pozycji, TP1/TP2, przejęciu pozycji i błędach krytycznych.

### 2.8. Przejście na prawdziwe konto (dopiero po testach)
W `config/config.yaml` ustaw `mode: live` i `live_confirm: true`, a w `.env` `BYBIT_API_KEY` /
`BYBIT_API_SECRET` z bybit.com (tylko handel, ograniczenie IP). Bez `live_confirm: true` bot odmówi startu.

---

## 3. Logika strategii

### 3.1. Moduły scoringu (każdy daje ocenę -100 = silny short … +100 = silny long)

| Moduł | Waga | Składniki | Uzasadnienie wagi |
|---|---|---|---|
| Trend | **25%** | struktura HH/HL vs LH/LL + Break of Structure, EMA 20/50/200 (ułożenie), ADX i ±DI; 1h 30% / 4h 40% / 1d 30% | najbardziej trwała przewaga na kryptowalutach (time-series momentum), dlatego największa waga |
| Momentum | **15%** | RSI (wygaszany w strefach wykupienia i wyprzedania), histogram MACD i jego nachylenie, regularne dywergencje RSI na potwierdzonych pivotach (1h i 4h) | potwierdza trend, ale jest szybszy i bardziej zaszumiony |
| Wolumen | **15%** | CVD z realnych transakcji (strona agresora), dywergencja CVD z ceną, RVOL w kierunku świecy, pozycja ceny względem Volume Profile (POC, VAH, VAL z 30 dni) | weryfikuje, czy ruch jest niesiony realnym przepływem |
| Pozycjonowanie | **15%** | OI razem z ceną (nowe longi/shorty vs. zamykanie), funding (kontrariańsko), long/short ratio z-score (kontrariańsko), klastry likwidacji (magnes) | informacja o tłoku i paliwie do squeeze'u |
| Order book | **10%** | imbalance ±0,5/1/2% (wagi 0,5/0,3/0,2), ściany utrzymujące się ≥30 s, spoofing (ściana znika przy podejściu ceny), potwierdzenie z Binance/OKX/Coinbase/Kraken | najszybciej się zmienia i łatwo nim manipulować, więc ma niską wagę |
| Makro | **10%** | 30-dniowa korelacja BTC z US500 i złotem, reżim US500 (SMA50 i zwrot 20 dni), ucieczka do złota przy spadających akcjach | filtr wolny; wpływa na wynik tylko przy istotnej korelacji |
| Sentyment | **10%** | Fear & Greed: poniżej 20 kontrariańsko plus, powyżej 80 kontrariańsko minus i ostrzeżenie w logu; w przedziale 20-80 wpływ słaby | skrajności są użyteczne, środek przedziału to szum |

Wynik końcowy to średnia ważona dostępnych modułów (wagi renormalizowane, gdy któryś moduł
jest niedostępny). Dla pary BTC/ETH wagi są osobne (`scoring.pair_weights`), a moduły działają
relatywnie: CVD BTC minus CVD ETH, różnica fundingu i L/S, risk-off na korzyść BTC,
skrajny strach na korzyść BTC.

**Wolumen tylko realny:** dane wyłącznie z Bybit, Binance, OKX, Coinbase i Kraken. Jeśli skok
wolumenu (RVOL ≥ 2) na Bybit nie jest potwierdzony na co najmniej 2 innych giełdach, oznaczam go
jako podejrzany i obniżam wagę RVOL do 0,3 (ostrzeżenie trafia do logu decyzji).

### 3.2. Reguły wejścia (ocena na zamknięciu świecy 1h)
**LONG** (dla shorta reguły są lustrzane):
1. score ≥ **+30** (`entry.threshold`),
2. **1d (reżim):** trend 1d > -20. Jeśli trend 1d < -20 (pozycja przeciw trendowi 1d), wymagany jest
   score ≥ **+55** (`strong_threshold`) i pozycja dostaje **połowę standardowego ryzyka**,
3. **4h (struktura):** trend 4h ≥ 0,
4. **1h (timing):** zamknięcie nad EMA20(1h) i rosnący histogram MACD(1h),
5. ≥ 3 moduły zgodne z kierunkiem (|s| ≥ 10) i najwyżej 1 moduł silnie przeciwny (|s| ≥ 50),
6. plan SL/TP z **R:R ≥ 2,0** (sekcja 3.4); po cenie faktycznego wejścia R:R jest sprawdzane ponownie.

### 3.3. Kiedy NIE handlować
- **sprzeczne sygnały:** trend 1h i 4h przeciwne i oba |s| ≥ 30, za mało zgodnych modułów albo za dużo silnie przeciwnych,
- **niska płynność:** RVOL < 0,35; w trybie live także spread > 5 bps albo głębokość ±1% < 2 mln USD,
- **skrajna zmienność:** ATR%(1h) powyżej 95. percentyla z 90 dni albo ostatnia świeca > 3× ATR,
- **dane makro z USA:** blokada od 60 min przed do 45 min po publikacji (kalendarz online high-impact USD,
  lista w `config/macro_events.yaml` i automatyczny NFP),
- dzienny lub tygodniowy limit straty przekroczony, wyczerpany budżet ryzyka, cooldown 3h po wyjściu z instrumentu.

### 3.4. Stop loss i take profit
**SL** (`signals/levels.py`):
1. kandydaci: swing low 1h/4h/1d poniżej wejścia (pivot potwierdzony po 3 świecach) minus bufor 0,3× ATR(1h);
2. wybieram najbliższego kandydata z odległością w przedziale **1-4× ATR(1h)**. Gdy struktura jest za blisko,
   SL = wejście - 1× ATR (czyli pod strukturą). Gdy brak struktury (nowe minima), SL = 2× ATR.
   Gdy struktura jest dalej niż 4× ATR, rezygnuję z transakcji (punkt unieważnienia za daleko);
3. **likwidacje:** jeśli w promieniu ±0,5 ATR od SL leży klaster likwidacji, przesuwam SL **za klaster**.
   Klastry przyciągają cenę (stop hunt), więc SL wewnątrz klastra zostałby zebrany.

**TP:**
- *przeszkody:* swing high 4h/1d, VAH/POC/VAL, ściany ask w order booku; *magnesy:* klastry likwidacji
  shortów, swing high 1h, HVN z Volume Profile, poziomy z Coinglass. Każdy poziom wyprzedzam o 0,1 ATR,
- jeśli najbliższa przeszkoda leży bliżej niż 2R, nie ma transakcji (R:R za niskie),
- **TP2** (cel główny, to od niego liczę R:R transakcji) = pierwszy poziom ≥ 2R; gdy brak poziomów, 3R,
- **TP1** = pierwszy poziom w przedziale 1,2R … R(TP2); **TP3** (runner) = pierwszy poziom ≥ R(TP2)+1, maksymalnie 8R,
- **częściowe zamykanie:** 35% na TP1, 35% na TP2, 30% runner. Po TP1 SL idzie na break-even + 0,15%
  (pokrywa prowizje), po TP2 włączam trailing stop 3× ATR(1h) (natywny trailing Bybit).

**Wcześniejsze wyjście** (scenariusz unieważniony, sprawdzane co godzinę): score przeciwny ≤ -25,
trend 4h przeciwny ≤ -35, zamknięcie 1h za poziomem struktury, na którym oparto SL, albo time stop
(72h bez osiągnięcia +0,5R).

### 3.5. Para BTC/ETH
Relacja syntetyczna: świece BTCUSDT/ETHUSDT. Sygnał long BTC/ETH otwiera **long BTCUSDT + short ETHUSDT**
o równej wartości (short BTC/ETH odwrotnie). Ryzyko liczone na SL ratio, z 4 egzekucjami (prowizja i poślizg),
z budżetem 0,75% (dwie nogi to ryzyko rozjazdu). SL i TP ratio pilnuje bot (co 10 s), a **każda noga ma
twardy SL na giełdzie** (4× dystans SL ratio lub 3× ATR4h nogi, większa z tych wartości). Gdy jedna noga
zostanie zamknięta, bot natychmiast zamyka drugą; nieudane otwarcie drugiej nogi też zamyka pierwszą.

---

## 4. Zarządzanie ryzykiem (zasady nienaruszalne)

| Zasada | Implementacja |
|---|---|
| max **1%** ryzyka na pozycję | `qty = (kapitał × 1%) / (|wejście − SL| + wejście·(prowizja+poślizg) + SL·(prowizja+poślizg))`, ilość zaokrąglana **w dół**. Kapitał pobierany na bieżąco z salda Bybit (`get_wallet_balance`). Twardy limit w kodzie: wartości >1% w configu są odrzucane przy starcie |
| R:R ≥ **2** | R(TP2) ≥ 2,0 sprawdzane przy planie i ponownie po cenie wejścia. `min_rr < 2` w configu jest odrzucane |
| łączne ryzyko ≤ **3%** | suma ryzyk do SL wszystkich pozycji (pozycja z SL na break-even ma ryzyko 0), liczona liniowo, bez „zysku z dywersyfikacji”, bo w krachu korelacje BTC/ETH dążą do 1 |
| korelacja BTC/ETH | pozycje w tym samym kierunku na BTC i ETH (korelacja z 30 dni ≥ 0,6) liczone jako jeden klaster, **max 2%**. W trybie one-way para i pojedyncze pozycje na tych samych instrumentach wykluczają się |
| dzienny limit **3%**, tygodniowy **6%** | spadek kapitału (z niezrealizowanym PnL) od początku dnia/tygodnia UTC. Po przekroczeniu brak nowych pozycji do nowego dnia/tygodnia |
| SL na giełdzie od początku | zlecenie market zawsze z `stopLoss` (`tpslMode=Full`, wyzwalanie ceną mark). Bez SL zlecenie nie zostanie wysłane. Po otwarciu weryfikacja: brak SL → `set_trading_stop`, a gdy to się nie uda → natychmiastowe zamknięcie. Co 10 s sprawdzam, czy każda pozycja ma SL |
| margin **isolated** | ustawiane przy starcie (UTA: `set_margin_mode ISOLATED_MARGIN`, konto klasyczne: per symbol); bez isolated bot nie startuje |
| dźwignia | `L = min(10, 1 / (2,5 × SL% + MMR))`, więc odległość do likwidacji ≥ 2,5× odległość do SL. Po otwarciu sprawdzam `liqPrice` z giełdy; gdy jest za blisko, pozycja jest zamykana |
| restart | `get_positions` → pozycje ze stanu są dalej zarządzane, a nieznane są **przejmowane**: dostają SL (strukturalny albo 2× ATR), TP i trafiają pod zarządzanie |

---

## 5. Decyzje projektowe (krótkie uzasadnienia)

- **pybit (oficjalny SDK Bybit V5)** do handlu i danych Bybit, **CCXT** tylko do innych giełd: oficjalna biblioteka szybciej wspiera nowe pola V5.
- **Dane do analizy z mainnetu nawet w trybie testnet** (`exchange.market_data_venue: mainnet`): testnet ma sztuczny wolumen i płytki order book. Poziomy SL/TP są przeliczane procentowo na cenę testnetu przed złożeniem zlecenia.
- **Jedna implementacja dla backtestu i live:** te same funkcje cech, scoringu, decyzji i SL/TP. Cechy są indeksowane czasem zamknięcia świecy i łączone `merge_asof backward`. Test (`tests/test_backtest.py::test_features_no_lookahead`) porównuje cechy liczone na danych uciętych i pełnych.
- **SL wyzwalany ceną mark**, TP ceną last: mark price jest odporna na pojedyncze knoty i manipulację last price.
- **TP1 i TP2 jako zlecenia limit reduce-only** (prowizja maker, nie zależą od działania bota), **TP3 jako `takeProfit` pozycji**, trailing natywny Bybit. Wszystko działa także, gdy bot jest offline.
- **Klastry likwidacji:** własny model estymujący (przyrost OI rozłożony na dźwignie 10/25/50/100x, usuwanie poziomów, przez które przeszła cena, wygaszanie). Działa bez płatnego API i w backteście. Coinglass (opcjonalny) i websocket `allLiquidation` uzupełniają go w trybie live.
- **Backtest konserwatywny:** wejście na otwarciu kolejnej świecy z poślizgiem; gdy w jednej świecy padają SL i TP, liczę najpierw SL; luka za SL wypełnia się po cenie otwarcia; funding co 8h; prowizje taker 0,055% i maker 0,02%; poślizg 0,05%.
- **Ograniczenia danych historycznych:** API Bybit nie udostępnia historii order booka, transakcji (CVD) ani likwidacji z websocketu. W backteście moduł order book jest pominięty (wagi renormalizowane), CVD liczę ze świec (CLV × wolumen), a klastry likwidacji z modelu OI. OI i L/S są opóźnione o 1h (konserwatywnie). Weryfikacja wolumenu na innych giełdach działa tylko live.
- **Walk-forward:** okna 180 dni trening → 60 dni test. Mała siatka (próg wejścia 25/30/35/40 × min R:R 2,0/2,5), kryterium SQN z minimalną liczbą transakcji, przy remisie wygrywają parametry domyślne. Osobno hold-out: ostatnie 20% danych nieużywane do żadnego doboru.
- **Limity ryzyka liczone liniowo** (bez dywersyfikacji): w krachu korelacje rosną, więc konserwatywnie.
- **Tryb one-way:** para BTC/ETH i pojedyncze pozycje BTC/ETH się wykluczają, bo na Bybit w one-way pozycje na tym samym symbolu by się zsumowały.
- **Awaria dodatkowego źródła** (CCXT, Coinglass, yfinance, alternative.me, kalendarz) nie zatrzymuje bota: każde źródło ma retry lub backoff, a moduł bez danych jest pomijany (wagi renormalizowane), z ostrzeżeniem w logu. Websocket ma watchdog (brak wiadomości > 60 s → ponowne połączenie).

---

## 6. Testy

```bash
pytest            # 44 testy: ryzyko i wielkość pozycji (27), backtest (8), egzekucja i bot (9)
```
- `tests/test_risk.py`: wielkość pozycji z prowizjami i poślizgiem, zaokrąglanie, dźwignia i likwidacja za SL, limity 1%/3%, klaster BTC-ETH, limity dzienny/tygodniowy, połowa ryzyka przeciw trendowi, twarde limity configu,
- `tests/test_backtest.py`: mechanika SL/TP/BE/trailing/luk, księgowanie, brak lookahead,
- `tests/test_execution.py`: **atrapa API Bybit V5** (`tests/fake_bybit.py`) waliduje parametry jak Bybit (stringi, strona SL względem ceny, reduce-only, „not modified”). Sprawdzane są: zlecenie zawsze ze `stopLoss`, zamknięcie przy zbyt bliskiej likwidacji, przejęcie pozycji bez SL po restarcie, przywrócenie usuniętego SL, BE po TP1, trailing po TP2, para (nieudana druga noga zamyka pierwszą, twardy SL nogi zamyka drugą), pełny cykl bota oraz `testnet_check`.

---

## 7. Ograniczenia i ostrzeżenia
- Wyniki backtestu zależą od okresu; przeszłe wyniki nie gwarantują przyszłych. Parametry ustaliłem z założeń, nie dopasowywałem ich do danych.
- Historia long/short ratio w API Bybit może być krótsza niż 2 lata; wtedy składnik jest pomijany tam, gdzie brak danych.
- Heatmapa Coinglass wymaga płatnego planu; bez niego bot używa własnego modelu.
- Kalendarz makro: feed online obejmuje bieżący tydzień; daty CPI/FOMC uzupełniaj w `config/macro_events.yaml`.
- Przejmowanie po restarcie obsługuje pozycje pojedyncze. Nogi pary otwarte przez bota są odtwarzane ze `logs/state.json`; bez tego pliku zostaną przejęte jako dwie osobne pozycje (każda z SL).
