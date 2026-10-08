# 🎣 One More Cast i 🐦 Pigeon Heist: dwa pomysły na grę, rozpisane szczegółowo

Oba pomysły są **oryginalne**. Zainspirowały je dane z analizy 35 gier z lat 2025–2026.
- Opisuję, jak się w nie gra, co zrobić w pierwszych tygodniach, jak je promować, ile można realnie zarobić i co może pójść nie tak.
- *Liczby z „~” to szacunki. Stan na 8 października 2026.*

---

## ⚖️ Porównanie w skrócie

| | 🎣 One More Cast | 🐦 Pigeon Heist |
|---|---|---|
| **Gatunek** | Rogalik dla jednego gracza typu „push your luck” | Co-op online dla 2–4 znajomych („friendslop”) |
| **Wzory z rynku** | CloverPit (2 osoby, 1 mln+ kopii), planszówka *Szarlatani z Pasikurowic*, Balatro | Meccha Chameleon, How to Fish, Gamble With Your Friends, PEAK |
| **Trudność z AI** | **łatwa** (5/5) | **średnia** (3–4/5), bo trudny jest multiplayer |
| **MVP (grywalny prototyp)** | ~3 tygodnie | ~4 tygodnie |
| **Gra gotowa do premiery** | 3–5 miesięcy | 6–9 miesięcy |
| **Koszt narzędzi** | ~150–500 $ (MVP) / ~1,5–5 tys. $ (pełna gra) | ~300–900 $ (MVP) / ~3–12 tys. $ (pełna gra) |
| **Cena** | 4,99–6,99 $ | 6,99–7,99 $ (na start ~4,95 $) |
| **Sufit zarobku** | wysoki | bardzo wysoki |
| **Ryzyko** | średnie | wysokie |
| **Najtrudniejsze** | balans i uczucie „jeszcze tylko jeden raz” | sieć, synchronizacja i testy w grupach |

---

# 🎣 CZĘŚĆ 1: ONE MORE CAST

### Pomysł w jednym zdaniu

> **Blackjack z rybami: przy każdym rzucie decydujesz, czy wyciągnąć jeszcze jedną rybę, i ryzykujesz cały połów.**

**Jak to wygląda na 15-sekundowym klipie:** linka napina się coraz mocniej, skrzypi, serce bije. Gracz klika „ciągnij” jeszcze raz… i wychodzi złota ryba z mnożnikiem ×50 albo rekin przecina linkę. Podpis pod filmikiem: *„Ciągnąłbyś dalej?”*

### Dlaczego to może zadziałać

- **CloverPit** zrobiły **2 osoby** z Włoch. Gra sprzedała **1 mln+ kopii w niecałe 2 miesiące**, zarobiła ~8 mln $ na samym Steamie, a potem trafiła do Game Passa, na telefony i konsole.
- **Emocje hazardu bez hazardu.** Uczucie „jeszcze tylko raz” bez prawdziwych pieniędzy. Ryby zamiast kart i automatów to plus, bo grafika kasynowa potrafi podnieść kategorię wiekową (głośny przypadek *Balatro*).
- **Mechanika sprawdzona od lat w planszówkach.** W *Szarlatanach z Pasikurowic* wyciągasz żetony z worka, a za dużo białych kończy się wybuchem kociołka. Tutaj: worek ze stworzeniami z jeziora, a za duże napięcie = pęknięta linka.
- **Gra dla jednego gracza.** Nie ma multiplayera, czyli nie ma największego ryzyka technicznego.
- **Mało grafiki.** Jedna scena i ikony stworzeń. Logikę punktów i zasad AI pisze bardzo dobrze.
- **Ryby są w modzie:** How to Fish, Cast n Chill, Webfishing.

### Jak się gra

1. **Dzień:** masz 3 rzuty wędką.
2. **Rzut:** wyciągasz z „worka jeziora” po jednym stworzeniu. Każde ma **wartość** (monety) i **napięcie** (0–5).
3. Gdy **suma napięcia przekroczy wytrzymałość linki** (na start 7), linka pęka i **tracisz cały połów z tego rzutu**.
4. W każdej chwili możesz **zwinąć** linkę i bezpiecznie zabrać połów.
5. **Wieczorem sklep:**
   - **przynęty:** dodają nowe stworzenia do worka;
   - **wabiki:** stałe zasady, które zmieniają grę;
   - **lepsze wędki:** większa wytrzymałość linki;
   - **patroszenie:** usuwanie słabych stworzeń z worka.
6. **Co 3 dni** przychodzi **Pan Sum** (szef przetwórni ryb, gadający sum w garniturze) po haracz. Nie masz pieniędzy, to koniec gry.

**Przykładowy rzut** (linka wytrzymuje 7):

| Wyciągnięcie | Stworzenie | Wartość | Napięcie | Razem |
|---|---|---|---|---|
| 1 | Płotka | +2 | 1 | 1/7 |
| 2 | Węgorz | +5 | 2 | 3/7 |
| 3 | Krab → wabik *„Węgorz obok kraba ×2”* | +3 (+5 premii) | 1 | 4/7 |
| 4 | **Złota Rybka** 🌟 | +20 | 0 | 4/7 |
| 5 | Szczupak | +8 | 3 | **7/7, na krawędzi!** |
| 6? | *Ciągniesz dalej?* Jeśli wyjdzie cokolwiek z napięciem, linka pęka i tracisz 43 monety | | | |

To właśnie ten moment („ciągnąć czy zwinąć?”) jest sercem gry i każdego klipu.

### Przykładowa zawartość

**Stworzenia (worek):**
| Stworzenie | Co robi |
|---|---|
| Płotka | Pospolita i bezpieczna, ale mało warta |
| Złota Rybka | Rzadka, dużo warta, zero napięcia |
| Szczupak | Dużo warty, ale ciężki (napięcie 3) |
| **Rekin** | Napięcie 5, prawie zawsze zrywa linkę |
| Rozgwiazda | Kopiuje poprzednie stworzenie |
| Ośmiornica | Wyciąga od razu dwa kolejne stworzenia |
| Stary But | Śmieć: 0 monet, napięcie 1 |
| Ryba-Bomba | Zeruje napięcie, ale niszczy połowę połowu |

**Wabiki (stałe zasady, „relikty”):**
| Wabik | Efekt |
|---|---|
| Ławica | 3 te same ryby w jednym rzucie = ×3 |
| Łańcuch pokarmowy | Drapieżnik zjada poprzednią rybę i dodaje jej wartość ×2 |
| Szczęśliwy Haczyk | Co 5. wyciągnięcie nie dodaje napięcia |
| Gumowa Linka | Pierwsze pęknięcie danego dnia się nie liczy |
| Chciwość | +1 do mnożnika za każde wyciągnięcie powyżej 80% napięcia |
| Konserwa | Śmieci są warte po 5 monet |

**Zakres: MVP kontra premiera**
| Element | MVP (~3 tygodnie) | Premiera (3–5 miesięcy) |
|---|---|---|
| Jeziora | 1 (Nocne Jezioro) | 5 (Bagno, Arktyka, Rafa, Kanały, Otchłań) |
| Stworzenia | 20 | 80+ |
| Wabiki | 15–25 | 120+ |
| Przynęty | 6 | 30 |
| Haracze/bossowie | 1 (Pan Sum) | 5 + tryb nieskończony |
| Meta | brak | odblokowania, Rybopedia, codzienne wyzwanie |

### Klimat, grafika i dźwięk

- **Klimat „cozy-creepy”:** nocne molo, latarnia, mgła, nad wodą świecą oczy czegoś dużego.
- **Grafika:** pixel art 2D albo ręcznie malowane 2D. Wystarczy jedna scena plus ikony stworzeń.
- **Dźwięk:**
  - skrzypienie linki, które rośnie razem z napięciem;
  - bicie serca przy wysokim ryzyku;
  - plusk i „brzdęk” monet;
  - muzyka: spokojny lo-fi albo jazz.

### Technologia i rola AI

| Co | Narzędzie | Kto to robi |
|---|---|---|
| Silnik | **Godot 4** (darmowy, lekki, eksport na PC, Maca, telefony i przeglądarkę) | — |
| Logika gry, sklep, zapis, testy zasad | **Claude Code** | 🤖 AI |
| Stworzenia i wabiki | pliki danych (dodajesz zawartość bez programowania) | 🤖 AI + Ty |
| Ikony stworzeń | PixelLab / Retro Diffusion + poprawki w Aseprite | 🤖 AI + Ty |
| **Okładka i główne grafiki na Steam** | zamówione u grafika (~200–800 $) | 👤 człowiek |
| Dźwięki | ElevenLabs | 🤖 AI |
| Muzyka | Suno Pro (płatny plan daje prawa komercyjne) | 🤖 AI |
| **Balans, „czucie” napięcia, testy z ludźmi** | — | 👤 **tylko Ty** |

### Plan MVP: 3 tygodnie

**Tydzień 1, „szare pudełka” (bez grafiki):**
- worek, wyciąganie, napięcie, pękanie linki, zwijanie;
- cykl dnia i haracz Pana Suma;
- 20 stworzeń i 15 wabików w plikach danych;
- testy automatyczne punktacji (napisze je Claude).

**Tydzień 2, „soczystość”:**
- scena mola, ikony, animacja linki;
- dźwięk narastającego napięcia;
- wyskakujące liczby i trzęsienie ekranu przy pęknięciu;
- sklep i 25 wabików.

**Tydzień 3, testy i strona:**
- 10–20 testerów (itch.io + Discord);
- zapis każdej rozgrywki do pliku, żeby widzieć, gdzie gracze przegrywają;
- balans: cel to ~30% wygranych gier;
- strona na Steamie i 10 nagranych klipów.

### Promocja: konkretnie

- **Klipy typu „Ciągnąłbyś dalej?”:** pauza w kulminacyjnym momencie, a ludzie kłócą się w komentarzach, co nakręca zasięg. Dalej: *„Ostatnie wyciągnięcie i… REKIN”*, *„Ten zestaw wabików zepsuł grę (×1000)”*.
- **Integracja z czatem Twitcha:** *„Czat decyduje: ciągnąć czy zwinąć?”*. Gra jest jednoosobowa, ale streamer gra „z widzami”, a to dla streamerów magnes.
- **Codzienne wyzwanie:** ten sam worek dla wszystkich i ranking, więc ludzie porównują wyniki i wracają.
- **Darmowe demo + Steam Next Fest.** Do tego **Fishing Fest** na Steamie (w 2025 roku: 16–23 czerwca; przyszłe daty sprawdź w kalendarzu wydarzeń Steam). *Cast n Chill* wystartował właśnie w trakcie tego festiwalu.
- **Wydawca od rogalików** (np. Future Friends, który wydał CloverPit) i pokazy typu Triple-i.

### Cena i model zarobku

- **Steam:** 4,99–6,99 $ z rabatem 20–38% na start, demo za darmo.
- **Później:**
  - wersja na telefony (premium 2,99–4,99 $);
  - Switch przez partnera od portów;
  - płatne DLC z nowymi jeziorami.
- **Bez reklam i mikropłatności.**

### Konkurencja

| Gra | Co to jest | Wniosek |
|---|---|---|
| CloverPit | Automat do gry + horror | Inna mechanika i temat; dowód, że nisza płaci |
| Fishing Fever (Gut Punch Studio) | Rogalik/deckbuilder o łowieniu, jeszcze niewydany | Nisza „ryby + rogalik” zaczyna się zapełniać |
| Deep Fishing | „Zejdź głębiej albo wróć z łupem”, w przygotowaniu | Podobny dylemat ryzyka, więc warto ruszyć szybko |
| Lake of Creatures (2024) | Rogalik z fizycznym zarzucaniem wędki | Inna mechanika |
| Lucky Punk | Deckbuilder „push your luck”, nie o rybach | Ta sama emocja, inny temat |

**Wyróżnik:** napięcie linki i worek (jak w *Szarlatanach*) + decyzje czatu Twitcha + klimat nocnego jeziora.

**Uwaga na nazwę:** nie znalazłem gry o tytule „One More Cast”, ale tak nazywa się **marka sprzętu wędkarskiego**, program TV i podcast. Istnieje też gra *One More Fishing*. Rozważ inną nazwę (np. *Line Snap*, *Reel Greed*, *Just One More Cast*) i sprawdź znaki towarowe (EUIPO, USPTO), zanim wydasz pieniądze na logo.

### Ryzyka

- **Zalew klonów Balatro:** bez wyraźnego haka zginiesz w tłumie.
- **Balans:** za łatwo jest nudno, za trudno frustruje. Potrzeba dziesiątek testów.
- **Grafika z AI:** około 25% graczy w USA chętniej omija gry z AI. Okładkę i główne ilustracje zrób ręcznie albo zamów.

### Ile można zarobić (scenariusze poglądowe)

Przy cenie 5,99 $ z jednej sprzedanej kopii zostaje **~2,9 $**: po rabatach, cenach regionalnych, 30% prowizji Steama i zwrotach, ale przed podatkiem.

| Scenariusz | Kopie | Przychód brutto | Zostaje (przed podatkiem) |
|---|---|---|---|
| Typowy debiut | ~2 000 | ~9 tys. $ | **~6 tys. $** |
| Dobry wynik | ~30 000 | ~135 tys. $ | **~88 tys. $** |
| Hit (poziom CloverPit) | ~1 000 000 | ~4,5 mln $ | **~2,9 mln $** |

⚠️ Większość debiutów kończy się w pierwszym wierszu. Dlatego liczy się tempo i kolejne gry, a nie jeden strzał.

---

# 🐦 CZĘŚĆ 2: PIGEON HEIST

### Pomysł w jednym zdaniu

> **Cztery gołębie, jeden tort weselny i bardzo zły dozorca parku.**

**Jak to wygląda na 15-sekundowym klipie:** cztery gołębie machają skrzydłami jak szalone, niosąc pizzę nad fontanną. Jeden przestaje machać, pizza ląduje w wodzie, a na czacie głosowym wszyscy krzyczą na tego jednego.

### Dlaczego to może zadziałać

- **Friendslop to najmocniejszy format 2025–2026:**
  - *How to Fish* (2 osoby): 1 mln kopii w 2 dni.
  - *Meccha Chameleon* (2 osoby, 2 miesiące): 20 mln kopii.
  - *Gamble With Your Friends* (~4 osoby): 2 mln w miesiąc.
  - *RV There Yet?* (4 osoby, nieco ponad 2 miesiące): 4,5 mln+.
- **Zwierzęta + fizyka + chaos = najlepsze klipy.** Zwierzęta dominowały wśród hitów: koty, kaczki, małpy, kameleony.
- **Gołębie zna każdy:** kradnące frytki i bezczelne. Humor jest zrozumiały w każdym kraju bez tłumaczenia.
- **Jeden kupujący = paczka 4 znajomych**, stąd tak wysokie wyniki tanich gier co-op.

### Jak się gra (runda 6–8 minut)

1. **Start** w gnieździe na dachu.
2. **Zwiad:** lecisz nad parkiem i szukasz jedzenia (piknik, stoiska, turyści upuszczający przekąski).
3. **Kradzież:** małe rzeczy niesiesz sam, **duże tylko razem**.
4. **Ucieczka:** dozorca z miotłą, rozbiegane dzieci, później pies.
5. **Powrót do gniazda** = okruchy (punkty).
6. **Co 3 rundy** (jeden „dzień”) **Don Gruchacz**, gołębi ojciec chrzestny ze złotym łańcuchem, żąda haraczu. Nie ma? Koniec gry. (Graczom *Lethal Company* i *R.E.P.O.* ten schemat jest dobrze znany.)
7. **Między dniami:** sklep z mocniejszymi skrzydłami, większym wolem i czapkami.

**⭐ Mechanika, która robi klipy sama: wspólne machanie**
- Ciężkie jedzenie unosi się tylko wtedy, gdy **kilka gołębi machnie w tym samym momencie** (okno ~0,3 sekundy).
- Gracze muszą liczyć na głos: *„raz, dwa, MACH!”*.
- Ktoś się spóźni? Tort przechyla się i spada.
- Dodatkowo „przeciąganie liny”: gołębie ciągną w różne strony, a pizza kręci się w powietrzu.

**Łupy (MVP):**
| Łup | Ile gołębi | Punkty | Haczyk |
|---|---|---|---|
| Okruszki | 1 | 1 | Szybkie i bezpieczne |
| Frytka | 1 | 3 | Inne ptaki próbują ją odebrać |
| Croissant | 1 | 8 | Spowalnia lot |
| Bagietka | 2 | 20 | Długa, obraca się na wietrze |
| Pizza | 3 | 40 | Kapie ser i zostawia ślad dla dozorcy |
| **Tort weselny** | **4** | **100** | Potrzeba wszystkich i idealnego machania |

**Umiejętności (MVP):**
- **Machnięcie / szybowanie:** zużywa wytrzymałość.
- **Gruchanie:** odwraca uwagę człowieka na 2 sekundy.
- **„Bomba z powietrza”:** dozorca się poślizguje (odnowienie 20 sekund).

**Przeciwnicy:**
- **Dozorca:** patroluje → zauważa → goni → uderza miotłą. Gołąb leci jak szmaciana lalka i upuszcza łup.
- **Dzieci:** wbiegają w stado i rozganiają gołębie.
- **Później:** pies, siatka, a na koniec dnia „deratyzator” z furgonetką.

**Mapy:** Park (MVP) → Targ → Wesele → Stadion → **Lotnisko** (wielki finał: wózek z jedzeniem w samolocie).

**Czapki (kosmetyka):** korona, mafijny kapelusz, kawałek pachołka drogowego, kromka chleba.

### Klimat, grafika i dźwięk

- **Grafika:** kreskówkowe, kolorowe low-poly 3D. Jeden model gołębia plus kolory i czapki.
- **Muzyka:** jazzowa, „skokowa”, w klimacie filmów o włamaniach.
- **Dźwięki:** gruchanie (najlepiej nagrane samemu, to darmowe i zabawne), łopot skrzydeł, „bonk” miotły.

### Technologia i rola AI (najważniejsza część)

| Co | Rekomendacja |
|---|---|
| Silnik | **Unity 6** (najwięcej gotowych rozwiązań co-op; na Unity powstały PEAK, YAPYAP i najpewniej How to Fish) albo Godot 4 + GodotSteam |
| Sieć | **Steam**: lobby, zaproszenia znajomych, przekaźnik połączeń; bez własnych serwerów i bez opłat. Biblioteka Netcode for GameObjects lub FishNet + Facepunch.Steamworks |
| Czat głosowy | Na start Discord. Później głos przestrzenny w grze (Steam Voice, Vivox albo Dissonance) |
| Kod sieciowy, AI przeciwników, menu | **Claude Code** |
| Rekwizyty 3D (jedzenie, ławki, stoiska) | Meshy / Tripo + paczki assetów (np. Kenney, darmowe) |
| Dźwięki i muzyka | ElevenLabs, Suno Pro |
| **Model gołębia, okładka** | 👤 ręcznie albo na zamówienie |
| **„Czucie” machania, testy w 4 osoby, łapanie desynchronizacji** | 👤 **tylko Ty i testerzy** |

**4 zasady, żeby multiplayer nie zabił projektu:**
1. **Gospodarz rządzi fizyką.** Tylko komputer hosta symuluje jedzenie, a pozostali widzą płynną kopię.
2. **Gołębie to postacie, nie bryły fizyczne**, więc dużo łatwiej je zsynchronizować.
3. **Ragdolle, pióra i okruchy to tylko lokalne efekty.** Nie synchronizujemy ich.
4. **Najwyżej ~20 synchronizowanych obiektów** na mapie.

👉 **Test przez internet z kolegą najpóźniej w 5. dniu.** Jeśli działa źle, upraszczasz od razu, a nie po 3 miesiącach.

### Zakres: MVP kontra premiera

| Element | MVP (~4 tygodnie) | Premiera (6–9 miesięcy) |
|---|---|---|
| Mapy | 1 (Park) | 4–5 |
| Łupy | 6 | 25+ |
| Przeciwnicy | dozorca + tłum | 5–6 typów |
| Umiejętności | 3 | 6–8 + ulepszenia |
| Czapki | 5 | 40+ |
| Głos | Discord | głos przestrzenny w grze |

### Plan MVP: 4 tygodnie

**Tydzień 1, najpierw sieć (najwyższe ryzyko):**
- lobby na Steamie i zaproszenia znajomych;
- 4 gołębie chodzą, machają i szybują zsynchronizowane;
- jeden łup niesiony przez 2–4 graczy;
- **test przez internet do piątku.**

**Tydzień 2, pętla gry:**
- park z paczki assetów i rekwizytów;
- dozorca (patrol → wypatrzenie → pościg → miotła);
- 6 łupów z wagą, gniazdo i punkty, czas rundy;
- ekran wyników z „najlepszą wpadką rundy”.

**Tydzień 3, śmiech:**
- ragdolle, gruchanie i emotki;
- „bomba z powietrza”;
- wspólne machanie z premią;
- czapki za okruchy i haracz Dona Gruchacza.

**Tydzień 4, testy grupowe:**
- co najmniej 3 grupy po 4 osoby;
- naprawa desynchronizacji;
- nagrywanie klipów z testów;
- strona na Steamie i zapisy do Steam Playtest;
- start **cotygodniowych devlogów**.

### Promocja: konkretnie

- **Klipy** (TikTok, Shorts, Reels), w każdym nazwa gry na ekranie:
  - *„4 gołębie kontra tort weselny”*;
  - *„Kiedy twój kumpel nie macha”*;
  - *„Dozorca nas nienawidzi”*;
  - *„Ukradliśmy CAŁĄ pizzę”*.
- **Przepis How to Fish:** co tydzień krótki klip z jedną nową rzeczą, przez wiele miesięcy przed premierą.
- **Darmowy Steam Playtest:** grupy znajomych testują i same nagrywają klipy.
- **Klucze dla małych i średnich streamerów friendslop.** Zadbaj o czytelny interfejs, tryb streamera i muzykę bez problemów z prawami autorskimi.
- **Demo + Next Fest.** Gry co-op słabo zamieniają granie w demo na wishlisty (analiza Chrisa Zukowskiego), więc w menu dema daj **duży przycisk „Dodaj do listy życzeń”**.
- **„Patron”:** Evil Landfall (zainwestował w How to Fish), kolektywy takie jak TENSTACK albo wspólne paczki z innymi grami friendslop.
- **Premiera:** 6,99–7,99 $, rabat ~38% w pierwszym tygodniu, paczka 4 kopii.

### Konkurencja

| Gra | Co to jest | Wniosek |
|---|---|---|
| **The Greatest Penguin Heist of All Time** | Co-op (1–8 graczy), fizyczny skok pingwinów; Early Access od 2021 (serwisy podają też datę 3.06.2026, prawdopodobnie pełnej wersji) | **25 tys. kopii do stycznia 2022**, ~2,9 tys. recenzji „Bardzo pozytywne”, cena 14,99 $, rekord tylko 261 graczy naraz. **Sam pomysł „zwierzęta + wspólny skok” nie wystarczy.** Potrzebna jest cena impulsowa, mechanika, która robi klipy, i fala streamerów |
| Pigeon Fight (2017) | Lokalna walka o chleb | Stara, lokalna, inny gatunek |
| Pigeon Protocol (2023) | Do 10 graczy, budowanie gniazd | Inny cel gry |
| Pigeon: A Love Story (sierpień 2026) | Lot nad miastem w poszukiwaniu miłości, z trybem co-op | Spokojna gra, nie chaos |

**Nazwa:** nie znalazłem gry „Pigeon Heist” (jest tylko gra fabularna *Pigeon's Eleven*). Mimo to sprawdź znaki towarowe przed premierą.

### Ryzyka

- **Multiplayer to ryzyko nr 1:** desynchronizacja, lagi, błędy, których sam nie wyłapiesz. Dlatego testy przez internet od pierwszego tygodnia.
- **Potrzebujesz 4 testerów naraz**, więc Discord zakładasz od początku.
- **Tłok na rynku:** co tydzień wychodzą nowe gry co-op, a hity gasną po 3–9 miesiącach. Plan na szybkie aktualizacje i nowe mapy.
- **Wysoki sufit, ale większość gier co-op sprzedaje się słabo.**

### Ile można zarobić (scenariusze poglądowe)

Lista 6,99 $, ale większość sprzedaży idzie w rabacie startowym i cenach regionalnych. Średnio ~4,5 $ brutto za kopię, czyli **~2,9 $ zostaje** (przed podatkiem).

| Scenariusz | Kopie | Przychód brutto | Zostaje (przed podatkiem) |
|---|---|---|---|
| Typowy debiut co-op | ~1 500 | ~7 tys. $ | **~4 tys. $** |
| Dobry wynik | ~50 000 | ~225 tys. $ | **~146 tys. $** |
| Hit (poziom Gamble With Your Friends) | ~2 000 000 | ~9 mln $ | **~5,9 mln $** |

---

# 🧭 CZĘŚĆ 3: Co bym zrobił na Twoim miejscu

**Krok 1. Szybki test haków (2 tygodnie)**
- Zrób dwa **bardzo proste** prototypy, po 3–5 dni każdy:
  - **One More Cast:** sam worek, napięcie i pękająca linka.
  - **Pigeon Heist:** wystarczy wersja dla jednego gracza z jednym gołębiem i pizzą, bez sieci.
- Wrzuć **po 5–6 krótkich klipów z każdego** na TikToka i YouTube Shorts.
- Mierz wyświetlenia, komentarze *„jak się nazywa ta gra?”* i zapisy na Discordzie.
- Tak zaczynał *YAPYAP*: viralowy TikTok miał, zanim gra była w ogóle grywalna.

**Krok 2. Wybór**
- **Domyślnie:** One More Cast jako **pierwsza gra**. Jest krótsza, tańsza i bez multiplayera, więc nauczysz się całego procesu wydania na Steamie przy małym ryzyku.
- **Pigeon Heist jako druga, większa gra.** Zaczniesz ją z gotową społecznością i doświadczeniem.
- **Wyjątek:** jeśli klipy z gołębiami wystrzelą (dziesiątki tysięcy polubień), idź za nimi od razu. Tak zrobili twórcy *How to Fish* i *RV There Yet?*.

**Krok 3. Zasada nadrzędna**
- Jeśli klipy nie chwytają, **zmieniaj hak, a nie silnik**.
- Promocję zaczynasz w dniu, w którym zaczynasz grę, a nie miesiąc przed premierą.

---

*Źródła i dane:*
- *Analiza 35 gier* jest w `games_analysis.xlsx`, `report.md` i `wpis_pl.md` w tym folderze.
- *Konkurencja:* sprawdzona w wyszukiwarce 8 października 2026. Wykorzystane strony: Steam (*Fishing Fever*, *Deep Fishing*, *Lake of Creatures*, *Lucky Punk*, *Pigeon Fight*, *Pigeon Protocol*), GamingOnLinux i Steambase (*The Greatest Penguin Heist of All Time*), Game Developer (*Pigeon: A Love Story*).
- *Uwaga:* scenariusze zarobku to przykłady obliczeń, a nie prognozy.
