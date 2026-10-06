# Agregator ofert pracy: wykonalność, prawo, konkurencja, rynek i MVP

**Stan wiedzy na 6 października 2026 r.** Rynek docelowy: Polska, potem ewentualnie reszta Europy. Wariant ogólny i niszowy (studenci, staże, praca dorywcza, praca zdalna).

**Oznaczenia w tekście:**
- **[F]** fakt ze źródłem (link w tekście, rok w nawiasie),
- **[S]** szacunek autora z jawnymi założeniami,
- **[O]** opinia lub ocena autora.

> ⚖️ **Zastrzeżenie prawne.** Część prawna to najlepsza dostępna ocena, a nie porada prawna. Przed startem komercyjnym, a zwłaszcza przed pobieraniem danych z cudzych serwisów, skonsultuj model z prawnikiem od IP i RODO. Pytania do prawnika są w Załączniku B.

---

## 0. Podsumowanie (10 zdań)

1. **[O]** Sama technologia nie jest problemem: z Claude Code zbudujesz działający agregator w kilka tygodni, a infrastruktura MVP kosztuje rzędu kilkuset złotych miesięcznie. Wąskim gardłem jest legalny dostęp do danych i dystrybucja.
2. **[F]** Najważniejsze źródła w Polsce (Pracuj.pl, OLX Praca, LinkedIn, Indeed, Just Join IT, No Fluff Jobs, Glassdoor, Facebook) nie udostępniają publicznego API do odczytu ofert, a ich regulaminy zakazują automatycznego pobierania lub kopiowania treści. Legalnie i tanio podłączysz głównie feedy partnerskie agregatorów (Adzuna, Jooble, Careerjet, Talent.com), publiczne endpointy systemów ATS (Greenhouse, Lever, Recruitee, Teamtailor), publiczną bazę ePraca (po ustaleniu warunków) oraz oferty dodawane bezpośrednio przez pracodawców.
3. **[F/O]** Ochrona baz danych sui generis w UE i wyroki TSUE (Innoweb, 2013; CV‑Online Latvia, 2021) sprawiają, że systematyczne kopiowanie ofert z dużych portali niesie realne ryzyko prawne. Model „fakty + krótki opis + link do oryginału, bez danych kontaktowych rekruterów” to ryzyko obniża, ale go nie usuwa.
4. **[F/O]** Wariant ogólny konkuruje z Jooble (ok. 4,06 mln wizyt z Polski w styczniu 2026), Grupą Pracuj (811,2 mln zł przychodu w 2025), LinkedIn, OLX i Google, dlatego oceniam jego szanse na **2/10**.
5. **[F]** Agregatory są pod presją: Joblift ogłosił niewypłacalność w kwietniu 2026 (aktywa przejęła Adzuna), Jooble zwolnił ok. 50 osób (2026), Monster i CareerBuilder złożyły wniosek o upadłość w czerwcu 2025, a ruch z wyszukiwarek przejmują AI Overviews i wyszukiwanie ofert w ChatGPT (na razie tylko w USA).
6. **[F/O]** Wariant niszowy („płatne staże i praca dla studentów”, start w Warszawie) trafia w realną lukę produktową. W Polsce jest 1,32 mln studentów (GUS, 2025/26), a ok. 80% pracuje w trakcie studiów (Eurostudent VIII, 2024). Oceniam go na **4/10 jako biznes** i **7/10 jako projekt edukacyjny i portfolio**.
7. **[S]** Monetyzacja jest trudna. Realistyczny miks przychodów to ok. 0,2–2 zł na aktywnego użytkownika miesięcznie, a płatne pozyskanie powracającego użytkownika kosztuje ok. 10–30 zł, więc wzrost musi być organiczny: SEO, uczelnie, organizacje studenckie, alerty.
8. **[S]** W scenariuszu bazowym (60 tys. MAU po 3 latach) projekt osiąga trwały miesięczny próg rentowności ok. 29. miesiąca, a skumulowany wynik po 3 latach wynosi ok. −23 tys. zł, przy nieopłacanej pracy założyciela w 1. roku.
9. **[O]** Rekomendacja: zacznij od 4–8-tygodniowego, prawie darmowego testu popytu. Uruchom newsletter i alerty „płatne staże i praca dla studentów w Warszawie” oparte wyłącznie o legalne źródła i przeprowadź 20 rozmów z pracodawcami. Portal buduj dopiero, gdy test przekroczy progi z sekcji 5.4.
10. Kwestie prawne opisane niżej to najlepsza dostępna ocena, ale przed startem komercyjnym wymagają konsultacji z prawnikiem.

---

## Metodologia i ograniczenia

- Analizę oparto na źródłach dostępnych przez wyszukiwarkę 6.10.2026. **Ograniczenie:** w środowisku, w którym powstała analiza, nie dało się bezpośrednio otworzyć części stron źródłowych (m.in. regulaminów LinkedIn, dokumentacji Adzuna i Jooble, serwisu curia.europa.eu). W takich miejscach opieram się na fragmentach stron wyświetlanych przez wyszukiwarkę lub na źródłach wtórnych i zaznaczam to. **Przed integracją każdego źródła przeczytaj jego aktualny regulamin** (lista kontrolna w Załączniku A).
- Kurs przeliczeniowy: **1 USD ≈ 3,7 zł**, 1 EUR ≈ 4,25 zł (założenie robocze, nie notowanie).
- Model finansowy jest w pliku [`model_finansowy.py`](./model_finansowy.py). Wszystkie liczby z sekcji 4 można przeliczyć po zmianie założeń.

---

## 1. Wykonalność techniczna

### 1.1. Dostęp do danych: platforma po platformie

| Platforma | Oficjalne API lub program partnerski (warunki, koszt, limity) | Feedy XML/JSON dla agregatorów | schema.org `JobPosting` | Regulamin a scraping; egzekwowanie | Ocena dostępu |
|---|---|---|---|---|---|
| **LinkedIn** | **[F]** Job Posting API wyłącznie dla partnerów LinkedIn Talent Solutions (głównie ATS). Działa jednokierunkowo: służy do publikowania ofert, nie do ich odczytu. Nowi partnerzy nie są przyjmowani i są kierowani do Apply Connect ([softgarden, 2025](https://support.softgarden.de/en/articles/700498-linkedin-basic-job-posting-via-api-is-blocked); [Microsoft Learn: Apply Connect](https://learn.microsoft.com/en-in/linkedin/talent/apply-connect)). | Nie. Feedy działają tylko w kierunku ATS → LinkedIn. | Publiczne strony ofert są indeksowane przez Google; znaczniki trzeba zweryfikować, np. Rich Results Test. | **[F]** [User Agreement](https://www.linkedin.com/legal/user-agreement) zakazuje botów i scrapingu. Egzekwowanie: hiQ zapłacił 500 tys. USD i przyjął stały zakaz (2022, [ZwillGen](https://www.zwillgen.com/alternative-data/hiq-v-linkedin-wrapped-up-web-scraping-lessons-learned/)). Proxycurl zamknięto po pozwie (VII 2025), a ProAPIs pozwano w X 2025 ([Security Affairs, 2025](https://securityaffairs.com/183001/security/linkedin-sues-proapis-for-15k-month-linkedin-data-scraping-scheme.html); [Bloomberg Law, 2025](https://news.bloomberglaw.com/ip-law/linkedin-battles-online-scrapers-in-perpetual-struggle-over-data)). | 🔴 Praktycznie niedostępne |
| **Indeed** | **[F, źródła wtórne]** Program Publisher/afiliacyjny zamknięty dla nowych od 2022 r., nowe klucze nie są wydawane ([Jobboardly, 2025](https://www.jobboardly.com/blog/indeed-affiliate-program); [jobspipe, 2026](https://jobspipe.dev/blog/indeed-publisher-api)). Obecne API (Job Sync API, Indeed Apply, Sponsored Jobs API) służą do **wysyłania** ofert i aplikacji przez zatwierdzonych partnerów ATS ([Indeed Docs: Job Sync FAQ](https://docs.indeed.com/job-sync-api/faq); [Indeed Apply dla ATS](https://docs.indeed.com/indeed-apply/ats)). | Nie dla agregatorów. Feed XML służy do wysyłania ofert do Indeed ([Indeed XML terms](https://docs.indeed.com/legal-terms/xml-api)). | Tak (Google for Jobs). | **[F]** Regulamin zakazuje automatycznego dostępu i budowania baz z treści Indeed ([ConductAtlas: Indeed ToS](https://conductatlas.com/platform/indeed/indeed-terms-of-service/provision/CA-P-028619/prohibition-on-scraping-automated-access-and-bot-activity/)). Serwis stosuje zabezpieczenia antybotowe. W Polsce Indeed jest słaby: 366 tys. realnych użytkowników w IV 2026 ([Gemius przez GoWork, 2026](https://www.gowork.pl/blog/?p=67777)). | 🔴 Niedostępne |
| **Glassdoor** | **[F, źródła wtórne]** Publiczne API wycofane (2021–2022). Dostęp tylko w ramach umów enterprise ([Zuplo, 2024](https://zuplo.com/learning-center/what-is-glassdoor-api)). Glassdoor działa w ramach Indeed/Recruit ([Recruit FY2025](https://recruit-holdings.com/en/ir/library/upload/Recruit_202603Q4_summary_en.html)). | Nie. | Tak. | **[F]** Regulamin zakazuje scrapingu ([ConductAtlas: Glassdoor ToU](https://conductatlas.com/platform/glassdoor/glassdoor-terms-of-use/provision/CA-P-027567/prohibition-on-automated-scraping-or-data-mining/)). | 🔴 Niedostępne |
| **Pracuj.pl** (+ theprotocol.it, od VII 2026 także No Fluff Jobs) | **[F]** Nie znalazłem publicznego API ani programu partnerskiego do **odczytu** ofert. Integracje istnieją po stronie publikacji (ATS i multiposting; eRecruiter należy do Grupy Pracuj). Cennik ogłoszeń: 299–599 zł netto w promocji dla nowych klientów (2026) ([Pracuj.pl: cennik](http://pracodawca.pracuj.pl/uslugi-i-cennik/ogloszenia-o-pracy/ogloszenie-standard/)). | Brak publicznych feedów. | Prawdopodobnie tak (obecność w Google for Jobs). **Do weryfikacji.** | **[O]** Regulaminu nie udało się otworzyć bezpośrednio, więc **zakładaj zakaz**. Na rynku działają nieoficjalne scrapery ([Apify](https://apify.com/trev0n/pracuj-pl-scraper)), ale to nie oznacza legalności. Ochrona sui generis jest bardzo prawdopodobna, bo portal ponosi duże nakłady na weryfikację i prezentację ofert (sekcja 2.1). | 🟠 Tylko umowa, mało prawdopodobna (bezpośredni konkurent) |
| **OLX Praca** | **[F]** OLX ma portal deweloperski (Partner API) do **publikowania** ogłoszeń. Aplikacje opisane jako „data scraping / competitor monitoring” są odrzucane ([Useme, 2025](https://useme.com/en/jobs/olx-bot-pomoc-w-rejestracji-aplikacji-w-portalu-deweloperskim-olx,131302/)). Multipublikacja przez eRecruiter wymaga pakietu Premium Ads ([eRecruiter](https://hrmarketplace.erecruiter.pl/en/partnerzy/multipublishing)). | Nie do odczytu. | Do weryfikacji. | **[F]** Regulamin zakazuje nieautoryzowanego scrapingu (źródło wtórne: [Thunderbit](https://thunderbit.com/pl/template/olx-scraper)). | 🔴 Niedostępne do odczytu |
| **Facebook** (grupy, Marketplace, strony) | **[F]** Facebook Jobs wyłączono poza USA i Kanadą od 22.02.2022 ([Element, 2022](https://elementapp.ai/blog/facebook-jobs-shutting-down-what-changes/)). Groups API wyłączono całkowicie 22.04.2024 ([Meta: Graph API v19](https://developers.facebook.com/docs/graph-api/changelog/version19.0/); [Ayrshare, 2024](https://www.ayrshare.com/blog/facebook-removes-groups-api-access-impact-and-implications/)). W X 2025 Meta przywróciła „Local Jobs” na Marketplace, na start tylko w USA ([iPhone in Canada, 2025](https://www.iphoneincanada.ca/2025/10/14/facebook-local-jobs-features); [Spider's Web, 2025](https://spidersweb.pl/2025/10/facebook-marketplace-oferty-pracy.html)). Meta Content Library jest dostępna tylko dla zatwierdzonych badaczy, w trybie „clean room” ([Meta Transparency](https://transparency.meta.com/researchtools/meta-content-library)). | [Jobs XML](https://developers.secure.facebook.com/docs/jobs-xml/specification) służy do **wysyłania** ofert przez partnerów. | Nie dotyczy. | **[F]** W USA scraping publicznych danych bez logowania nie naruszył regulaminu Meta (Meta v. Bright Data, 2024; [FBM](https://www.fbm.com/technology/publications/major-decision-affects-law-of-scraping-and-online-data-collection-meta-platforms-v-bright-data/)). Grupy wymagają jednak logowania, a posty prywatnych osób to dane osobowe (RODO). | 🔴 Niedostępne. Legalna droga: admin grupy albo pracodawca sam przesyła ofertę. |
| **Jooble** | **[F]** Darmowe REST API: klucz na wniosek, zapytanie POST z JSON, odpowiedź zawiera tytuł, firmę, lokalizację, fragment opisu, wynagrodzenie, źródło i link. Limity ustalane per klucz, brak publicznego cennika. API ma kierować ruch do Jooble ([Jooble API](https://jooble.org/api/about); opis: [jobspipe, 2026](https://jobspipe.dev/blog/jooble-api)). | Feed i API dla partnerów. | — | Korzystanie zgodnie z warunkami API. | 🟢 Legalne i tanie (ruch odpływa do konkurenta) |
| **Adzuna** | **[F]** Darmowe API, 16 rynków (w tym PL). Domyślne limity: 25 zapytań/min, 250/dzień, 1000/tydzień, 2500/miesiąc. Publikacja ofert jest dozwolona z oznaczeniem „Jobs by Adzuna” (logo i link). Inne użycie komercyjne: 14-dniowy okres próbny, potem może być potrzebna licencja. Bez zgody nie wolno używać danych w agregacji (np. średnie płace) ([Adzuna API ToS](https://developer.adzuna.com/docs/terms_of_service)). | API; wyższe limity po kontakcie. | — | Warunki API. | 🟢 Legalne i tanie (małe limity) |
| **Careerjet** | **[F]** Partner Program: widgety, Search API i feedy XML. Wydawca dostaje prowizję za kliknięcie; jest locale `pl_PL` ([klient API Careerjet](https://github.com/careerjet/careerjet-api-client-python); [Affililist](https://www.affililist.com/affiliate/careerjet)). | Tak. | — | Warunki programu. | 🟢 Legalne; płaci Tobie |
| **Talent.com** | **[F]** Publisher Program: feedy XML, samoobsługowe Job API i linki afiliacyjne. Rozliczenie CPC co miesiąc; ponad 30 mln ofert w 79 krajach ([Talent.com Publishers](https://employers.talent.com/publishers)). | Tak. | — | Warunki programu. | 🟢 Legalne; płaci Tobie |
| **GoWork.pl** | Nie znalazłem publicznego API. | Nie znaleziono. | Do weryfikacji. | Regulamin do weryfikacji. **[O]** Zakładaj zakaz. | 🟠 Umowa |
| **Praca.pl** | Nie znalazłem publicznego API do odczytu. Istnieją integracje ATS do publikacji ([Manatal](https://www.manatal.com/integrations/praca-pl)). | Nie znaleziono. | Do weryfikacji. | **[F]** Regulamin zakazuje kopiowania i reprodukowania materiałów serwisu ([Praca.pl: regulamin](https://www.praca.pl/regulamin.html)). | 🟠 Umowa |
| **Just Join IT / Rocket Jobs** | **[F, źródło wtórne]** Brak publicznego API ([Apify, 2026](https://apify.com/mrarcode/justjoinit-scraper)). | Nie. | Do weryfikacji. | Regulamin do weryfikacji. **[O]** Zakładaj zakaz. | 🟠 Umowa |
| **No Fluff Jobs** | Brak publicznego API (nie znaleziono). Od 24.07.2026 w Grupie Pracuj ([SIA, 2026](https://www.staffingindustry.com/news/global-daily-news/grupa-pracuj-acquires-polish-it-job-board-no-fluff-jobs)). | Nie. | Do weryfikacji. | Do weryfikacji. | 🟠 Umowa |
| **InfoPraca, Aplikuj.pl** | Brak publicznych API (nie znaleziono dokumentacji). | Nie znaleziono. | Do weryfikacji. | Do weryfikacji. | 🟠 Umowa. **[O]** Mniejsi gracze chętniej rozmawiają o wymianie ruchu. |
| **ePraca** (dawne CBOP; publiczna baza MRPiPS) | **[F]** Od 1.06.2025 baza ePraca zastąpiła CBOP. Pracodawcy z sektora publicznego mają obowiązek zgłaszać do niej oferty ([ustawa z 20.03.2025](https://isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20250000620/T/D20250620L.pdf); [PUP Pruszków](https://pruszkow.praca.gov.pl/strona-glowna/-/asset_publisher/6utRDu1650Nt/content/informacja-dla-pracodawcow-nowe-obowiazki-zwiazane-z-publikacja-ofert-pracy); [gov.pl: ePraca](https://www.gov.pl/web/rodzina/ePraca)). Publicznego API nie znalazłem. | Nie znaleziono; **zapytaj ministerstwo** o warunki ponownego wykorzystania. | — | Dane publiczne, ale zawierają kontakty (RODO). | 🟡 Legalne po ustaleniu warunków |
| **EURES** | **[F]** Przesyłanie ofert i dostęp maszynowy są przewidziane dla członków i partnerów sieci EURES ([decyzja wykonawcza 2017/1257](https://lexaris.de/book/version/documentflat/head/2031961)). | Dla członków i partnerów. | — | Do weryfikacji. | 🟡 Częściowo |
| **ATS: Greenhouse, Lever, Recruitee, Teamtailor** (+ Workable, SmartRecruiters) | **[F]** Publiczne endpointy tablic ogłoszeń bez klucza, np. `boards-api.greenhouse.io/v1/boards/{firma}/jobs`, `api.lever.co/v0/postings/{firma}`, `{firma}.recruitee.com/api/offers/`, `{firma}.teamtailor.com/jobs.rss` ([Nango: Greenhouse Job Board](https://nango.dev/docs/integrations/all/greenhouse-job-board.md); [DEV: Greenhouse API](https://dev.to/zsevic/integration-with-greenhouse-public-jobs-api-1lj3); [Lever Postings API](https://github.com/lever/postings-api)). | Tak (JSON/RSS). | Często tak na stronach kariery. | **[O]** Endpointy służą do pokazywania ofert danej firmy. Dalsze rozpowszechnianie przez stronę trzecią to szara strefa, więc **najlepiej uzyskać zgodę pracodawcy (opt-in)**. | 🟢 Tanie, niskie ryzyko przy zgodzie |
| **Google for Jobs** | Brak API do odczytu indeksu. `JobPosting` to format, w którym serwisy przekazują dane Google ([Google Search Central](https://developers.google.com/search/docs/appearance/structured-data/job-posting)). | — | — | — | Kanał dystrybucji dla **Twoich** ofert, nie źródło danych |

### 1.2. Znaczniki schema.org `JobPosting`: czy można z nich legalnie korzystać?

- **[F]** `JobPosting` w JSON-LD to warunek pojawienia się oferty w Google for Jobs. Wymagane pola to m.in. `title`, `description`, `datePosted`, `hiringOrganization`, `jobLocation` i `validThrough`. Dane w znacznikach muszą zgadzać się z treścią strony ([Google, 2026](https://developers.google.com/search/docs/appearance/structured-data/job-posting)). Google for Jobs działa w Polsce ([SEO for Jobs](https://www.seo-for-jobs.com/us/resources/in-which-countries-is-google-for-jobs-available)).
- **[O] Odczyt cudzych znaczników przez Twój crawler to z prawnego punktu widzenia scraping.** Format techniczny nie daje licencji. Obowiązują te same zasady: prawo sui generis do bazy, regulamin serwisu i RODO. Znaczniki ułatwiają parsowanie, ale nie legalizują pobierania z Pracuj.pl czy OLX.
- **[O]** Rozsądne użycie `JobPosting` jako źródła danych: **strony kariery pracodawców, którzy wyrazili zgodę**, albo serwisy, z którymi masz umowę.
- **[O] Konflikt z modelem „fragment + link”:** Google oczekuje na stronie pełnej treści oferty. Jeśli ze względów prawnych pokazujesz tylko fragment i przekierowujesz do źródła, Twoja strona słabo kwalifikuje się do Google for Jobs. Pełne opisy i znaczniki możesz bezpiecznie publikować tylko dla ofert dodanych bezpośrednio przez pracodawców. To argument za budową **własnej bazy ofert bezpośrednich**.

### 1.3. Facebook: czy dostęp jest w ogóle możliwy?

- **[F]** Grupy z ofertami pracy są w Polsce popularne i szybko rosną ([Maciej M., Substack](https://maciejm.substack.com/p/szybkie-wzrosty-grup-facebookowych)). Od 22.04.2024 nie ma jednak żadnego API grup ([Meta, 2024](https://developers.facebook.com/docs/graph-api/changelog/version19.0/)). Funkcja Jobs zniknęła poza USA i Kanadą w 2022 r., a nowe „Local Jobs” (X 2025) startowały tylko w USA.
- **[O]** Automatyczne czytanie grup wymagałoby konta, czyli akceptacji regulaminu z zakazem automatyzacji, i przetwarzania postów osób prywatnych. Ryzyko prawne i blokad jest wysokie, a wartość ofert niska (duplikaty, brak struktury).
- **Legalne alternatywy:** (1) partnerstwo z administratorami największych grup studenckich, którzy publikują Twoje zestawienia lub przesyłają oferty za zgodą autorów; (2) formularz „dodaj ofertę” promowany w tych grupach; (3) publikowanie własnych treści w grupach jako kanał pozyskiwania użytkowników, a nie źródło danych.

### 1.4. Realistyczne metody pozyskiwania ofert

| Metoda | Koszt | Skala w PL | Ryzyko prawne | Komentarz |
|---|---|---|---|---|
| Feedy i API partnerów (Adzuna, Jooble, Careerjet, Talent.com) | 0 zł; częściowo płacą Tobie za kliknięcia | Średnia–duża (oferty zebrane przez nich) | 🟢 Niskie przy przestrzeganiu warunków | Oferty te same co u konkurencji. Ruch częściowo „oddajesz” agregatorowi. |
| Oferty dodawane bezpośrednio przez pracodawców | 0 zł + sprzedaż | Mała na starcie | 🟢 Niskie; to **Twoja** baza z ochroną sui generis | Jedyna droga do unikalnej treści i pełnego `JobPosting`. Problem „zimnego startu”. |
| ATS i strony kariery firm, za zgodą | Niski (czas na wdrożenie) | Średnia: setki firm zatrudniających studentów | 🟢/🟡 Niskie z opt-in | Najlepszy stosunek jakości do ryzyka. Zacznij od 50–200 firm z Warszawy. |
| Publiczna baza ePraca, EURES | 0 zł | Średnia (sektor publiczny, praca fizyczna) | 🟡 Do ustalenia warunków; RODO | Dobra dla niszy „sektor publiczny”. |
| Biura karier i organizacje studenckie (wymiana ofert) | Czas | Mała–średnia | 🟢 Niskie z umową | Biura karier często korzystają już z JobTeaser lub własnych portali (sekcja 3). |
| `JobPosting` z cudzych portali (bez zgody) | Niski | Duża | 🔴 Wysokie (sui generis, regulamin) | Nie polecam. |
| Scraping dużych portali (Pracuj.pl, OLX, LinkedIn, Indeed, JJIT, NFJ) | Średni (proxy, utrzymanie) | Duża | 🔴 Wysokie: pozwy, blokady, RODO | Nie polecam. To najczęstszy błąd projektów tego typu. |
| Scraping grup FB | Średni | Mała | 🔴 Wysokie | Nie polecam. |

### 1.5. Podsumowanie dostępu do danych

- 🟢 **Legalnie i tanio:** API i feedy Adzuna, Jooble, Careerjet, Talent.com; publiczne tablice ATS (Greenhouse, Lever, Recruitee, Teamtailor, Workable, SmartRecruiters) za zgodą pracodawców; oferty dodawane bezpośrednio; Twoje własne strony z `JobPosting`.
- 🟡 **Wymaga ustalenia warunków lub umowy:** ePraca (ministerstwo), EURES, mniejsze portale (Aplikuj.pl, InfoPraca, Praca.pl, GoWork) w ramach wymiany ruchu lub afiliacji, biura karier.
- 🔴 **Praktycznie niedostępne:** LinkedIn, Indeed, Glassdoor, Pracuj.pl (z theprotocol.it i NFJ), OLX Praca, Just Join IT i Rocket Jobs bez umowy, Facebook.

**[O] Wniosek:** agregator „wszystkiego z polskich portali” nie powstanie legalnie bez umów z gigantami. Ci gigantowie są Twoimi konkurentami i nie mają powodu takich umów podpisywać.

### 1.6. Architektura techniczna

```
 Źródła                     Pobieranie (cron)             Przetwarzanie                    Serwowanie
┌──────────────────┐   ┌──────────────────────┐   ┌──────────────────────────┐   ┌─────────────────────┐
│ API partnerów    │──▶│ konektory per źródło │──▶│ 1. walidacja i surowy    │──▶│ wyszukiwarka        │
│ ATS (opt-in)     │   │ (limity, robots.txt, │   │    zapis (JSON)          │   │ (Meilisearch/       │
│ ePraca/EURES     │   │  retry, ETag)        │   │ 2. normalizacja (reguły  │   │  Typesense)         │
│ formularz        │   └──────────────────────┘   │    + LLM dla trudnych)   │   │ strony SEO z        │
│ pracodawcy       │                              │ 3. deduplikacja          │   │  JobPosting (tylko  │
└──────────────────┘                              │    (klucz + MinHash/LSH) │   │  oferty bezpośr.)   │
                                                  │ 4. scoring i wygaszanie  │   │ alerty e-mail/push  │
                                                  └──────────────────────────┘   └─────────────────────┘
                                         Postgres (np. Supabase): oferty, źródła, klastry duplikatów, użytkownicy
```

**Pobieranie.** Każde źródło ma osobny konektor uruchamiany przez cron (GitHub Actions, Supabase Cron albo mały VPS). Konektor respektuje limity API (np. Adzuna: 25 zapytań/min, 2500/mies.), `robots.txt`, nagłówki `ETag`/`Last-Modified` i ponawia zapytania z wykładniczym opóźnieniem. Surowe dane trafiają do tabeli `raw_offers` razem z identyfikatorem źródła i datą, co ułatwia audyt i odpowiedzi na zgłoszenia.

**Normalizacja** (najpierw reguły, potem LLM tylko dla trudnych przypadków):

| Pole | Jak normalizować | Uwagi |
|---|---|---|
| Stanowisko | Słownik synonimów i mapowanie do [ESCO](https://esco.ec.europa.eu/) (klasyfikacja UE). Wyodrębnij poziom: staż, junior, mid, senior. | Np. „Praktykant/ka”, „Stażysta”, „Intern” → staż. |
| Lokalizacja | Kody [TERYT](https://eteryt.stat.gov.pl/) + geokodowanie (lat/lng). Dzielnica dla Warszawy. | Umożliwia filtr „dojazd do kampusu”. |
| Widełki | Parsowanie zakresów; brutto/netto; UoP, B2B, umowa zlecenie; stawka godzinowa vs miesięczna; przeliczenie na miesięczne brutto w zł. | **[F]** Od 24.12.2025 pracodawca musi podać kandydatowi wynagrodzenie lub jego przedział, ale niekoniecznie w ogłoszeniu ([HRappka, 2026](https://hrappka.pl/blog/jawnosc-wynagrodzen/); [Bezprawnik](https://bezprawnik.pl/liczyliscie-na-jawnosc-wynagrodzen-w-ogloszeniach-o-prace-pracodawcy-wcale-nie-musza-ich-podawac/)). W I 2026 informację o płacy zawierało 59% ogłoszeń w OLX Praca ([Infor, 2026](https://kadry.infor.pl/kadry/hrm/rekrutacja/7603365,510-tys-zl-w-ogloszeniach-o-prace-jak-pracodawcy-radza-sobie-z-nowymi-przepisami-o-wynagrodzeniach.html)). |
| Tryb pracy | Zdalna, hybrydowa, stacjonarna; wymiar etatu; elastyczne godziny. | Kluczowe dla studentów. |
| Typ umowy | UoP, umowa zlecenie, umowa o dzieło, B2B, staż płatny lub niepłatny, praktyka. | **[F]** Student do 26 lat na umowie zlecenie nie podlega składkom ZUS ([Zielona Linia](https://zielonalinia.gov.pl/praca-studenta-a-skladki-do-zus/)), więc „na rękę” dostaje więcej. To wyróżnik filtrów niszowych. |

**[F] Koszt ekstrakcji LLM** (cennik Anthropic API, 2026: Claude Haiku 4.5 – 1 USD / 5 USD za 1 mln tokenów wejścia/wyjścia; Batch API −50%; [Anthropic pricing](https://docs.claude.com/en/docs/about-claude/pricing)). **[S]** Przy ok. 1200 tokenach wejścia i 250 tokenach wyjścia na ofertę: 10 tys. ofert/mies. kosztuje ok. 24,5 USD (12 USD w Batch API), a 50 tys. ok. 122 USD (61 USD w Batch API). LLM-em przetwarzaj tylko nowe, nieustrukturyzowane oferty, po deduplikacji.

**Deduplikacja** (ta sama oferta na kilku portalach):
1. Dokładne duplikaty: ten sam URL lub ID w źródle, ten sam hash znormalizowanych pól (firma, stanowisko, miasto, widełki).
2. Prawie duplikaty: MinHash + LSH na opisie (shingle 5-wyrazowe), potem reguły (ta sama firma, miasto ±, data ±7 dni). **[F]** Badania nad ogłoszeniami pokazują, że prawdziwe duplikaty mogą mieć podobieństwo tekstowe nawet tylko 37%, a firmy używają szablonów, w których 90% treści się powtarza. Sam próg podobieństwa nie wystarcza ([Skeptric: przegląd metod](https://skeptric.com/near-duplicate-review); [Textkernel](https://www.textkernel.com/newsroom/online-job-postings-have-many-duplicates-but-how-can-you-detect-them-if-they-are-not-exact-copies-of-each-other/); system Apollo w CareerBuilder: [IEEE ICDMW, 2017](https://computer.org/csdl/proceedings-article/icdmw/2017/3800a177/12OmNC17hUn)).
3. Przypadki graniczne rozstrzyga LLM (tanio, bo jest ich niewiele).
4. Wybór wersji kanonicznej: strona kariery pracodawcy > ATS > portal > agregator. Interfejs pokazuje „Ta oferta jest też na: …”.

**Indeksowanie i wyszukiwanie.** Meilisearch lub Typesense (fasety, tolerancja literówek, geowyszukiwanie) albo na start sam Postgres (FTS + `pg_trgm`). Ranking: świeżość, jawność widełek, kompletność, dopasowanie do profilu, jakość pracodawcy.

**Aktualizacja i wygaszanie.** Feedy i ATS synchronizuj co 6–24 h. Ofertę oznaczaj jako wygasłą, gdy: minął `validThrough`; zniknęła z feedu w 2 kolejnych synchronizacjach; źródło zwraca 404/410; nie została potwierdzona od 30 dni. Dodaj pracodawcy przycisk „zamknij ofertę” i formularz zgłoszenia nieaktualnej oferty. Linki sprawdzaj oszczędnie, żeby nie obciążać źródeł.

**Przybliżony koszt hostingu i utrzymania [S]** (ceny narzędzi z 2026: Supabase Pro 25 USD/mies. – [Jetadmin, 2026](https://www.jetadmin.io/blog/supabase-pricing-2026-guide-to-plans-limits-and-real-world-costs/); Meilisearch Cloud od ok. 15–30 USD/mies. – [PricingSaaS, 2026](https://pricingsaas.com/companies/meilisearch); Typesense Cloud od 14 USD/mies. lub self-hosting – [Tech Insider, 2026](https://tech-insider.org/?p=23180)):

| Składnik | MVP (do 10 tys. MAU) | Skala (100 tys. MAU) | Skala (500 tys. MAU) |
|---|---|---|---|
| Frontend (Vercel lub Cloudflare Pages) | 0–80 zł | 80–400 zł | 400–1500 zł |
| Baza danych (Supabase) | 0–95 zł | 95–600 zł | 600–2500 zł |
| Wyszukiwarka | 0–110 zł (self-host / plan podstawowy) | 200–800 zł | 800–3000 zł |
| Crawler i cron (VPS / GitHub Actions) | 0–90 zł | 90–300 zł | 300–1000 zł |
| E-mail i alerty | 0–80 zł | 200–800 zł | 800–3000 zł |
| LLM (normalizacja) | 50–100 zł | 100–300 zł | 300–1000 zł |
| **Razem / mies.** | **ok. 50–550 zł** | **ok. 0,8–3,2 tys. zł** | **ok. 3,2–12 tys. zł** |

**[O] Wariant no-code vs Claude Code.** No-code (Softr lub Glide + Airtable + Make/Zapier + Tally) wystarczy do testu popytu z kilkuset ofertami, ale dławi się przy deduplikacji i wyszukiwaniu tysięcy ofert. Przy Twoich umiejętnościach polecam od razu **Next.js + Supabase + Meilisearch + GitHub Actions**, pisane z Claude Code, a no-code tylko do formularzy i newslettera.

---

## 2. Aspekty prawne

### 2.1. Prawo baz danych (UE i Polska)

- **[F] Ramy:** dyrektywa 96/9/WE, art. 7 (prawo sui generis), oraz polska [ustawa z 27 lipca 2001 r. o ochronie baz danych](https://isap.sejm.gov.pl/isap.Nsf/download.xsp/WDU20011281402/U/D20011402Lj.pdf) ([tekst jedn. Dz.U. 2024 poz. 1769](https://eli.gov.pl/eli/DU/2024/1769/ogl/pol/pdf)). Ochrona przysługuje bazie, której sporządzenie, weryfikacja lub prezentacja wymagały **istotnego nakładu inwestycyjnego**. Producent ma wyłączne prawo do pobierania danych i ich wtórnego wykorzystania w całości lub w istotnej części. Ustawa zakazuje też **powtarzającego się i systematycznego** pobierania nieistotnych części, jeśli jest sprzeczne z normalnym korzystaniem z bazy i narusza słuszne interesy producenta. Wyjątki (art. 8) obejmują m.in. użytek osobisty z baz nieelektronicznych i dydaktykę lub badania **niekomercyjne**. Komercyjny agregator nie mieści się w nich.
- **[F] TSUE Innoweb v Wegener (C‑202/12, 2013):** wyspecjalizowana metawyszukiwarka ogłoszeń samochodowych (GasPedaal, ok. 100 tys. wyszukiwań dziennie) **może stanowić „wtórne wykorzystanie”**, bo daje dostęp do całej bazy inaczej, niż przewidział producent ([SCL, 2013](https://www.scl.org/2984-database-right-innoweb-v-wegener-cjeu-judgment/)).
- **[F] TSUE CV‑Online Latvia v Melons (C‑762/19, 3.06.2021):** sprawa dotyczyła **wyszukiwarki ogłoszeń o pracę** (KurDarbs.lv), która przekierowywała do źródłowego portalu cv.lv. Trybunał uznał, że pobieranie i wtórne wykorzystanie są zakazane, **jeśli pozbawiają producenta przychodów potrzebnych do zwrotu inwestycji**. Wprowadził też ważenie interesów: dostęp do informacji i konkurencja kontra ochrona inwestycji ([IPPT, 2021](https://www.ippt.eu/sites/ippt/files/2021/IPPT20210603_CJEU_CV-Online_Latvia_v_Melons.pdf); [Clifford Chance, 2021](https://cliffordchance.com/expertise/services/intellectual-property/global-ip-updates/2021/q4/cv-online-latvia-v-melons.html); [Kluwer Copyright Blog, 2021](https://copyrightblog.kluweriplaw.com/2021/06/17/access-to-information-and-competition-concerns-enter-the-sui-generis-rights-infringement-test-the-cjeu-redefines-the-database-right/?output=pdf)).
- **[F] TSUE Ryanair v PR Aviation (C‑30/14, 15.01.2015):** jeśli baza **nie** jest chroniona (ani prawem autorskim, ani sui generis), jej właściciel może swobodnie ograniczyć korzystanie **regulaminem**, w tym zakazać screen scrapingu ([Pinsent Masons, 2015](https://www.pinsentmasons.com/out-law/news/website-operators-can-prohibit-screen-scraping-of-unprotected-data-via-terms-and-conditions-says-eu-court-in-ryanair-case)). Brak ochrony bazy nie otwiera więc drogi do scrapingu, bo wtedy wiąże Cię umowa (regulamin).
- **[F] Polska:** SA w Szczecinie (I ACa 105/12, 2012) i SN (II CSK 466/12, 2013) w sprawie portalu ogłoszeń motoryzacyjnych uznały, że nakłady na ogłoszenia wpisywane przez samych użytkowników bez weryfikacji mogą nie wystarczyć. Inaczej oceniono jednak inwestycję w cały system ogłoszeń ([LGL, 2024](https://lgl-iplaw.pl/2024/03/ochrona-baz-danych-czyli-kiedy-przysluguje-ci-monopol-na-baze-danych-a-kiedy-nie-mozesz-zakazac-screen-scrapingu/)). Zob. też [PARP: web scraping](https://power.parp.gov.pl/component/content/article/83315:web-scraping-jak-prawidlowo-korzystac-z-tresci-dostepnych-w-internecie).
- **[F] TDM:** nowelizacja prawa autorskiego i ustawy o ochronie baz danych z 26.07.2024 (w mocy od 20.09.2024) wprowadziła wyjątek eksploracji tekstów i danych, z możliwością zastrzeżenia przez uprawnionego ([Chambers, 2024](https://chambers.com/articles/tdm-finally-in-the-polish-law); [Wolters Kluwer, 2024](https://www.wolterskluwer.com/pl-pl/expert-insights/tdm-ai-prawo-autorskie)). **[O]** TDM obejmuje analizę danych, np. statystykę rynku, a **nie** publikowanie ofert użytkownikom. Nie legalizuje więc agregatora.
- **[O] Wpływ na projekt:** Pracuj.pl, OLX czy JJIT prawie na pewno spełniają kryterium istotnej inwestycji (weryfikacja, moderacja, prezentacja). Systematyczne pobieranie ich ofert to scenariusz z Innoweb. Obroną z CV‑Online byłoby wykazanie, że kierujesz do nich ruch i nie podważasz ich przychodów. To jednak ocena faktów w konkretnej sprawie, a startup nie chce być stroną precedensu.

### 2.2. Spory i wyroki dotyczące scrapingu i agregatorów

| Sprawa (rok) | Jurysdykcja | Wynik | Znaczenie dla Ciebie |
|---|---|---|---|
| Innoweb v Wegener (2013) | TSUE | Metawyszukiwarka ogłoszeń może naruszać prawo sui generis | 🔴 Bezpośrednia analogia |
| CV‑Online Latvia v Melons (2021) | TSUE | Agregator ofert pracy narusza prawo tylko przy szkodzie dla inwestycji; ważenie interesów | 🟡 Częściowa obrona, zależna od faktów |
| Ryanair v PR Aviation (2015) | TSUE | Gdy baza nie jest chroniona, regulamin może zakazać scrapingu | 🔴 Regulaminy portali są skuteczne |
| BGH I ZR 224/12 „Flugvermittlung im Internet” (2014) | Niemcy | Screen scraping danych lotów **nie** był nieuczciwą konkurencją ([LTO, 2014](https://www.lto.de/recht/hintergruende/h/bgh-urteil-izr22412-screen-scraping-flugdaten-automatisiert-auslesen-ryanair-reiseportal)) | 🟢 Argument z prawa konkurencji, ale nie z prawa baz danych |
| hiQ v LinkedIn (2019–2022) | USA | CFAA zawężone, ale ostatecznie hiQ naruszył umowę: 500 tys. USD i stały zakaz ([Proskauer, 2022](https://newmedialaw.proskauer.com/2022/12/08/hiq-and-linkedin-reach-proposed-settlement-in-landmark-scraping-case/)) | 🔴 Regulamin = umowa |
| Meta v Bright Data (I 2024) | USA | Scraping publicznych danych **bez logowania** nie naruszył regulaminu ([Quinn Emanuel, 2024](https://www.quinnemanuel.com/the-firm/news-events/client-alert-meta-v-bright-data-significant-decision-for-web-scraping-industry/)) | 🟡 USA; w UE dochodzi RODO i prawo sui generis |
| Ryanair v Booking.com (VII 2024) | USA (Delaware) | Ława przysięgłych: Booking odpowiada z CFAA za screen scraping ([Bloomberg Law, 2024](https://news.bloomberglaw.com/litigation/ryanair-wins-jury-verdict-in-scraping-case-against-booking-com)) | 🔴 Duzi gracze wygrywają też w USA |
| LinkedIn v Proxycurl (VII 2025), v ProAPIs (X 2025) | USA | Proxycurl (wg założyciela ok. 10 mln USD przychodu) zamknięty; nowe pozwy ([Bloomberg Law, 2025](https://news.bloomberglaw.com/ip-law/linkedin-battles-online-scrapers-in-perpetual-struggle-over-data)) | 🔴 Agresywne egzekwowanie |
| CNIL v KASPR (XII 2024) | Francja (RODO) | 240 tys. EUR kary za zbieranie danych kontaktowych z LinkedIn ([CNIL, 2024](https://www.cnil.fr/en/data-scraping-kaspr-fined-eu240000)) | 🔴 Dane kontaktowe rekruterów |
| UODO v Bisnode (kara 2019; NSA 19.09.2023) | Polska (RODO) | 943 tys. zł za brak obowiązku informacyjnego (art. 14 RODO) wobec osób z publicznych rejestrów ([Prawo.pl, 2023](https://www.prawo.pl/kadry/pierwsza-kara-nalozona-przez-uodo-na-bisnode-wyrok-nsa,523262.html)) | 🔴 „Publicznie dostępne” ≠ „wolno przetwarzać bez obowiązków” |

**[F]** Nie znalazłem polskiego wyroku dotyczącego konkretnie agregatora ofert pracy. Najbliższe są sprawy portali ogłoszeniowych z sekcji 2.1.

### 2.3. RODO i dane osobowe w ofertach

- **[F/O]** Imię i nazwisko rekrutera, e-mail i telefon w ofercie to dane osobowe. Jeśli je kopiujesz i wyświetlasz, stajesz się **administratorem**. Wynikają z tego obowiązki: podstawa prawna (art. 6 ust. 1 lit. f, prawnie uzasadniony interes, z udokumentowanym testem równowagi), obowiązek informacyjny z art. 14 (sprawa Bisnode), minimalizacja, retencja, prawa osób, umowy powierzenia z dostawcami (hosting, e-mail) i transfery poza EOG (np. narzędzia z USA).
- **[F]** TSUE w sprawie KNLTB (C‑621/22, 4.10.2024) uznał, że interes **komercyjny** może być prawnie uzasadnionym interesem, ale przetwarzanie musi być niezbędne i przejść test równowagi ([Hunton, 2024](https://huntonak.com/privacy-and-information-security-law/cjeu-rules-on-scope-of-legitimate-interest-basis-under-the-gdpr)). Wcześniej holenderski organ AP twierdził, że scraping danych osobowych jest „prawie zawsze” niezgodny z RODO ([IAPP, 2024](https://iapp.org/news/a/netherlands-dpa-issues-guidance-against-web-scraping)).
- **[O] Rekomendacja:** **nie pobieraj i nie wyświetlaj danych kontaktowych osób.** Pokazuj tylko firmę i link do aplikowania u źródła. Dane użytkowników (konta, alerty) przetwarzaj na podstawie umowy (świadczenie usługi alertów), a marketing wysyłaj tylko za zgodą. Prowadź rejestr czynności przetwarzania, politykę prywatności i procedurę obsługi żądań.
- **[O]** Gdy dodasz dopasowywanie kandydatów do ofert przez AI, sprawdź art. 22 RODO (zautomatyzowane decyzje) i AI Act (sekcja 2.5).

### 2.4. Prawa autorskie, linkowanie, cytowanie, nieuczciwa konkurencja

- **[O]** Krótkie, faktograficzne ogłoszenie często nie jest utworem. Rozbudowane opisy, teksty employer brandingowe, grafiki i logo mogą być chronione. Bezpieczniej pokazywać **fakty** (stanowisko, firma, miasto, widełki, typ umowy) i **własne krótkie streszczenie** niż kopiować opis. Prawo cytatu (art. 29 pr. aut.) wymaga celu takiego jak wyjaśnianie, analiza czy krytyka i nie pasuje do masowego wyświetlania ofert.
- **[F] Linkowanie:** link do treści udostępnionej legalnie i swobodnie w internecie nie jest „nowym publicznym udostępnieniem” (Svensson, C‑466/12, 2014). Link do treści udostępnionej bezprawnie może naruszać prawo przy działaniu w celu zarobkowym (GS Media, C‑160/15, 2016). Framing obchodzący zabezpieczenia techniczne jest nowym udostępnieniem (VG Bild‑Kunst, C‑392/19, 2021) ([Dandi Media](https://www.dandi.media/en/european-court-justice-hyperlink/); [Cuatrecasas, 2021](https://www.cuatrecasas.com/en/global/art/cjeu-rules-internet-links-right-communication-public-vg-bild-kunst)). **Wniosek:** zwykły link do oryginalnej oferty jest bezpieczny. Nie osadzaj ofert w ramkach (iframe).
- **[F/O] Nieuczciwa konkurencja:** art. 3 [ustawy o zwalczaniu nieuczciwej konkurencji](https://api.sejm.gov.pl/eli/acts/DU/1993/211/text.html) (działanie sprzeczne z prawem lub dobrymi obyczajami, które zagraża interesowi innego przedsiębiorcy). Polska doktryna dopuszcza kwalifikowanie systematycznego „pasożytowania” na cudzym wysiłku jako czynu nieuczciwej konkurencji. Niemiecki BGH (2014) uznał natomiast screen scraping za dopuszczalny. Ryzyko istnieje i zależy od skali kopiowania oraz od tego, czy podszywasz się pod źródło.

### 2.5. DSA, AI Act i inne regulacje

- **[F] DSA:** jeśli pracodawcy lub użytkownicy publikują u Ciebie treści, jesteś usługą hostingu lub platformą internetową. Mikro- i małe przedsiębiorstwa (poniżej 50 osób i 10 mln EUR obrotu) są zwolnione z większości dodatkowych obowiązków platform (art. 19–28), ale muszą m.in. mieć punkt kontaktowy, jasny regulamin, mechanizm zgłaszania nielegalnych treści (art. 16) i uzasadniać moderację ([YPOG](https://www.ypog.law/en/insight/digital-services-act); [Presencis](https://presencis.com/regulations/dsa/applicability/)). **[F]** W Polsce prezydent zawetował pierwszą wersję ustawy wdrażającej w I 2026 ([Demagog, 2026](https://demagog.org.pl/na-biezaco/weto-do-ustawy-wdrazajacej-dsa-jakie-sa-argumenty-nawrockiego/)). W 2026 r. uchwalono i podpisano nową ustawę, która czyni **Prezesa UKE koordynatorem ds. usług cyfrowych** ([UKE, 2026](https://uke.gov.pl/uslugi-cyfrowe/aktualnosci/sejm-uchwalil-ustawe-wdrazajaca-przepisy-aktu-o-uslugach-cyfrowych-prezes-uke-koordynatorem-ds-uslug-cyfrowych,26.html); [XYZ, 2026](https://xyz.pl/?p=254266)). Według doniesień z chwili podpisania pierwszej ustawy druga, o nielegalnych treściach, była jeszcze na etapie prac w Sejmie (aktualny status sprawdź przed startem).
- **[F] AI Act:** systemy AI przeznaczone do rekrutacji, „w szczególności do umieszczania **ukierunkowanych ogłoszeń o pracę**”, analizy i filtrowania aplikacji oraz oceny kandydatów, to systemy **wysokiego ryzyka** (załącznik III pkt 4) ([AI Act, Annex III](https://artificialintelligenceact.eu/annex/3/)). Pakiet Digital Omnibus (przyjęty VI 2026, opublikowany w Dz.U. UE 24.07.2026) przesunął obowiązki dla systemów z załącznika III na **2.12.2027** ([FPF, 2026](https://fpf.org/blog/the-ai-act-implementation-timeline-what-changes-under-the-ai-omnibus/); [Gibson Dunn, 2026](https://www.gibsondunn.com/eu-ai-act-omnibus-agreement-postponed-high-risk-deadlines-and-other-key-changes/)). **[O]** Prosty filtr i sortowanie to nie „ukierunkowane ogłoszenia”. Spersonalizowane rekomendacje ofert oparte na profilu kandydata mogą już podpadać pod tę kategorię. Projektuj rekomendacje z myślą o tym terminie: dokumentacja, nadzór człowieka, testy uprzedzeń. Jeśli dodasz czatbota, informuj, że to AI (obowiązki przejrzystości AI Act).
- **[O] Inne:** rozporządzenie P2B 2019/1150 (przejrzystość rankingu wobec pracodawców publikujących oferty), prawo konsumenckie przy subskrypcjach premium (prawo odstąpienia w 14 dni), zgody na marketing e-mailowy, a w niszy stażowej przyszła **ustawa o stażach** (projekt MRPiPS z 20.04.2026: staż maks. 6 miesięcy, obowiązkowe świadczenie min. 35% przeciętnego wynagrodzenia, wejście w życie planowane w 2027 r.) ([Prawo.pl, 2026](https://www.prawo.pl/kadry/projekt-ustawy-o-stazach,536702.html); [Forsal, 2026](https://forsal.pl/praca/aktualnosci/artykuly/11233884,resort-pracy-chce-zmian-w-kwestii-bezplatnych-stazy-maksymalnie-6-miesiecy-i-tylko-z-wynagrodzeniem.html)). Równolegle trwają trilogi nad unijną dyrektywą stażową ([ICTU, VI 2026](https://www.ictu.ie/sites/default/files/users/user1261/2_June_2026_Minister_Peter_Burke_re_Traineeship_Directive.pdf)). **[O]** To szansa produktowa: filtr „staż zgodny z nowymi przepisami”.

### 2.6. Czy wystarczy linkować zamiast kopiować? Rekomendowany model

**[O] Samo linkowanie jest bezpieczne, ale problemem prawnym nie jest link, tylko sposób zdobycia danych do jego wyświetlenia.** Jeśli wyświetlasz tytuł, firmę i miasto pobrane automatycznie z bazy Pracuj.pl, to dokonałeś pobrania i wtórnego wykorzystania, nawet gdy kliknięcie prowadzi do Pracuj.pl.

**Model minimalizujący ryzyko:**
1. **Źródła:** wyłącznie licencjonowane feedy i API (z oznaczeniami wymaganymi przez partnera), ATS i strony kariery **za zgodą** firm, oferty bezpośrednie, ePraca po ustaleniu warunków. **Bez scrapingu** dużych portali i Facebooka.
2. **Prezentacja:** fakty (stanowisko, firma, miasto, widełki, typ umowy, tryb), własne 1–2 zdania streszczenia, wyraźne „Źródło: X” i zwykły link do oryginału. Bez ramek, bez kopiowania pełnych opisów cudzych ofert, bez logo bez zgody.
3. **RODO:** żadnych danych kontaktowych osób; test równowagi, polityka prywatności i procedura żądań.
4. **Zgłaszanie i usuwanie:** formularz i e-mail; usuwanie na żądanie w 24–48 h; logi źródła każdej oferty.
5. **Dokumenty:** regulamin (DSA), polityka prywatności, warunki dla pracodawców, rejestr czynności przetwarzania. **[S]** Koszt prawnika: ok. 3–8 tys. zł jednorazowo (szacunek, do sprawdzenia w 2–3 kancelariach). **[O]** Zapytaj też o bezpłatne konsultacje w uczelnianych inkubatorach przedsiębiorczości.
6. **Forma prawna:** na test popytu wystarczy działalność nierejestrowana. **[F]** Limit w 2026 r. to 10 813,50 zł przychodu na kwartał ([Money.pl, 2026](https://direct.money.pl/artykuly/porady/dzialalnosc-nierejestrowana-2026-limit-10-813,50-zl,-po-przekroczeniu-7-dni-na-ceidg)). Przy umowach z firmami i ryzyku prawnym rozważ później spółkę z o.o.

---

## 3. Konkurencja

### 3.1. Tabela konkurentów

RU = realni użytkownicy miesięcznie (Gemius/PBI, IV 2026, kategoria „praca”, [dane opublikowane przez GoWork](https://www.gowork.pl/blog/?p=67777)).

| Gracz | Model biznesowy i przychody | Skala | Skąd ma oferty | Mocne strony | Słabe strony i luki |
|---|---|---|---|---|---|
| **Indeed** (Recruit) | Sponsorowane oferty CPC, opłaty za aplikację; narzędzia AI | **[F]** HR Technology (Indeed + Glassdoor): 9,67 mld USD przychodu w FY2025 (IV 2025 – III 2026) ([Recruit, 2026](https://recruit-holdings.com/en/ir/library/upload/Recruit_202603Q4_earnings_en.html)). W PL tylko 366 tys. RU (IV 2026). | Pracodawcy, ATS (Job Sync) | Globalna skala, AI (Career Scout, Talent Scout – IX 2025, [Business Wire](https://www.businesswire.com/news/home/20250910809034/en/Indeed-Introduces-New-Suite-of-Hiring-Products-Career-Scout-Talent-Scout-Premium-Sponsored-Jobs-and-Indeed-Connect)) | Słaba pozycja w Polsce; brak filtrów studenckich |
| **Google for Jobs** | Brak opłat; utrzymuje ruch w Google (reklamy) | Działa w PL | Znaczniki `JobPosting` | Zero tarcia dla użytkownika, deduplikacja | Tylko oferty ze znacznikami; brak niszowych filtrów. **[F]** Skargi branży: 23 serwisy, w tym Adzuna (2019; [Recruiter](https://www.recruiter.co.uk/node/52062)), Jobindex (2022). KE nałożyła na Google 460 mln EUR kary z DMA za faworyzowanie własnych usług w wyszukiwarce (23.07.2026; komunikat wymienia zakupy, hotele, transport, sport) ([KE, 2026](https://cyprus.representation.ec.europa.eu/news/commission-fines-google-eur890-million-breaches-digital-markets-act-2026-07-23_en)) |
| **LinkedIn Jobs** | Płatne ogłoszenia, Recruiter (subskrypcje), Premium | **[F]** LinkedIn: 19,8 mld USD przychodu w FY2026 (+12%); agentowe narzędzia rekrutacyjne >450 mln USD rocznie ([LinkedIn, 2026](https://news.linkedin.com/2026/q4-earnings-and-business-highlights)). W PL 2,78 mln RU (IV 2026). | Pracodawcy, ATS | Profile kandydatów, sieć | Słaby w pracy fizycznej i studenckiej dorywczej |
| **Pracuj.pl** (Grupa Pracuj) | Płatne ogłoszenia (pakiety, e-commerce), ATS eRecruiter | **[F]** Grupa: 811,2 mln zł przychodu i 45,2% marży skor. EBITDA w 2025 ([Parkiet, 2026](https://www.parkiet.com/firmy/art44094121-grupa-pracuj-z-rekordem-przychodow-i-dywidendy)); H1 2026: 425,5 mln zł, segment Polska 309,3 mln zł ([PulsHR, 2026](https://www.pulshr.pl/zarzadzanie/rynek-rekrutacji-odbija-grupa-pracuj-zwieksza-przychody-i-marze,121366.html)); 762,8 tys. ofert i 61 762 aktywnych klientów w 2025 ([Bankier, 2026](https://www.bankier.pl/wiadomosc/W-25-w-serwisie-Pracuj-pl-opublikowano-762-8-tys-ofert-pracy-liczba-aplikacji-wzrosla-o-5-proc-rdr-9070308.html)); 3,08 mln RU | Bezpośrednio od pracodawców | Marka, white collar, ATS (eRecruiter: 2332 klientów w 2025, [Grupa Pracuj](https://ir.grupapracuj.pl/en/news/grupa-pracuj-hits-a-record-number-of-clients-delivering-growth-in-a-demanding-market)), konsolidacja (NFJ za 10,4 mln zł, VII 2026) | Słabszy w ofertach studenckich i dorywczych (rozwija pink i blue collar, [XYZ, 2026](https://xyz.pl/poland-unpacked/soft-markets-hard-targets-inside-pracuj-groups-long-term-bet-6718/)) |
| **OLX Praca** | Płatne ogłoszenia (cena dynamiczna) | **[F]** 2,01 mln RU (IV 2026) | Bezpośrednio | Blue collar, lokalność, praca sezonowa | Niska jakość i struktura ofert, brak filtrów studenckich |
| **GoWork.pl** | Employer branding (opinie), ogłoszenia | **[F]** 3,64 mln RU, lider kategorii (IV 2026) | Ogłoszenia + opinie | Zasięg SEO, opinie o pracodawcach | Kontrowersje wokół anonimowych opinii ([Substack](https://maciejm.substack.com/p/drama-gowork-czy-model-biznesowy)) |
| **Jooble** | CPC (sprzedaż przekierowań), promowanie ofert | **[F]** ok. 4,06 mln wizyt z PL w I 2026, Polska to 11,47% ruchu globalnego ([Semrush, 2026](https://semrush.com/website/jooble.org/overview)); 1,93 mln RU „Grupa Jooble CIS” (IV 2026); zwolnienia ok. 50 osób (2026, [DOU](https://dou.ua/lenta/news/layoffs-in-jooble/)) | Agregacja (crawling, feedy) | Skala, SEO, 60+ krajów | Ogólny charakter, presja na marże |
| **Adzuna** | CPC, dane (API, raporty płac) | **[F]** Przychody szacowane na 15–31 mln USD (2025; [Prospeo](https://prospeo.io/c/adzuna-revenue)); przejęła aktywa Joblift (VII 2026, [Dealroom](https://dealroom.co/news/139700-adzuna-acquires-insolvent-german-jobs-startup-joblift/)) | Agregacja, feedy | API i dane, konsolidacja | Słaba rozpoznawalność w PL |
| **Talent.com** (dawniej Neuvoo) | CPC, program wydawców | **[F]** 120 mln USD (seria B, 2022); >30 mln ofert, 78–79 krajów ([Recruiting News Network, 2022](https://www.recruitingnewsnetwork.com/posts/talent-com-raises-120m-series-b)) | Crawling stron kariery i ATS | Feedy dla wydawców | Generyczny produkt |
| **Jobrapido** | CPC | **[F]** 58 krajów; od 2014 r. własność STG ([Journalism.co.uk](https://www.journalism.co.uk/daily-mail-publisher-dmgt-buys-italian-recruitment-search-engine-jobrapido/); [Google case study](https://developers.google.com/search/case-studies/jobrapido-case-study)) | Agregacja | SEO | Generyczny |
| **Careerjet** | CPC + program partnerski | Brak aktualnych danych o skali | Agregacja | Partner API dla wydawców | Generyczny |
| **Glassdoor** | Opinie, employer branding | Zintegrowany z Indeed (FY2025) | Indeed | Opinie, płace | Słaby w PL |
| **Praca.pl** | Pakiety ogłoszeń 649–1649 zł netto ([Praca.pl](https://www.praca.pl/nasze-uslugi)) | **[F]** 893 tys. RU (IV 2026) | Bezpośrednio | Regiony | Mniejsza skala |
| **Just Join IT / Rocket Jobs** | Płatne ogłoszenia od 99 zł ([StronyBiznesowe](https://stronybiznesowe.pl/blog/gdzie-dac-ogloszenie-o-prace)) | **[F]** JJIT: 110 996 ofert w 2025 (+8,4%) ([Antyweb, 2026](https://antyweb.pl/rynek-pracy-it-2026)); Rocket Jobs: 712,8 tys. RU (IV 2026) | Bezpośrednio | UX, jawne widełki | Nisza IT nasycona |
| **No Fluff Jobs** | Płatne ogłoszenia | **[F]** ok. 25 tys. aktywnych ofert/mies., ok. 530 tys. użytkowników/mies.; przejęty przez Grupę Pracuj za 10,4 mln zł (VII 2026) ([SIA, 2026](https://www.staffingindustry.com/news/global-daily-news/grupa-pracuj-acquires-polish-it-job-board-no-fluff-jobs)) | Bezpośrednio | Obowiązkowe widełki | Konsolidacja |
| **Aplikuj.pl** | Płatne ogłoszenia | **[F]** 1,03 mln RU (IV 2026) | Bezpośrednio | Zasięg regionalny | — |
| **InfoPraca** | Płatne ogłoszenia | Brak danych | Bezpośrednio | — | — |
| **JobTeaser** (nisza studencka) | Licencje dla uczelni + oferty firm | **[F]** >700 uczelni w Europie; w PL m.in. UW, UAM, UŚ, UMK, US (dane sprzed 2023 r., [PolishScience](https://www.polishscience.pl/en/?p=245042)) | Biura karier, firmy | Wbudowany w uczelnie | Słaba widoczność poza uczelnią; mało ofert dorywczych |
| **Absolvent.pl** (nisza) | Employer branding, targi | Ok. 2 tys. ofert (dane archiwalne, [Rzeczpospolita](https://www.rp.pl/poszukiwanie-pracy/art5024961-mlodym-polakom-bedzie-latwiej-o-prace-i-staz)) | Bezpośrednio | Wydarzenia | Programy dla absolwentów, mniej dorywczych |
| **ePraca** (państwowa) | Bezpłatna | Oferty urzędów pracy i sektora publicznego | Urzędy pracy | Darmowa, obowiązkowa dla sektora publicznego | Słaby UX |
| **CrawlJobs / Jobs.pl** (nowy gracz) | Agregacja AI | **[F]** 3 mln USD zalążkowej rundy (III 2026); inwestycja w Jobs.pl ([Raising.fi, 2026](https://raising.fi/news/crawljobs-seed-march-2026); [XYZ, 2026](https://xyz.pl/?p=234101)) | Crawler stron pracodawców | Kapitał, technologia | Wczesny etap |
| **ChatGPT (wyszukiwanie ofert)** | Ekosystem OpenAI | **[F]** Oferty z Indeed, Upwork, Appcast; tylko USA, edytor CV globalnie ([The Decoder, 2026](https://the-decoder.com/openai-turns-chatgpt-into-a-career-platform-with-job-search-and-cv-editor/)) | Partnerzy | Interfejs AI | Na razie tylko USA |

**Projekty, które upadły lub się wycofały, i przyczyny:**

| Projekt | Co się stało | Przyczyna |
|---|---|---|
| **Joblift** (DE, agregator) | Niewypłacalność IV 2026; aktywa kupiła Adzuna VII 2026. **[F]** Przychody spadły z 16 mln EUR (2022) do 10,5 mln EUR (2023), strata 6,4 mln EUR; od 2019 finansowany pożyczkami pomostowymi ([SIA, 2026](https://www.staffingindustry.com/news/global-daily-news/adzuna-acquires-assets-of-germanys-joblift)) | Uzależnienie od płatnego i organicznego ruchu, presja cenowa CPC, brak unikalnej podaży |
| **Monster + CareerBuilder** | Wniosek o upadłość (Chapter 11), VI 2025 ([6abc, 2025](https://6abc.com/post/monster-careerbuilder-popular-job-seekers-file-bankruptcy/16844808/)) | Utrata użytkowników na rzecz Indeed i LinkedIn, słaby rynek |
| **GoldenLine** (PL) | Wyłączony 30.11.2024; spółka nierentowna od lat (poza 2021) ([ITwiz, 2024](https://itwiz.pl/?p=61770)) | Konkurencja LinkedIn i Pracuj.pl, brak modelu monetyzacji |
| **Hired** (US) | Wchłonięty przez LHH (Adecco) w 2024 po wyprzedaży ([LongBoard](https://longboard-hcmacquisitions.beehiiv.com/p/hcm-acquisition-news-hiredcom-update-learn-favorite-influencer-will-help-find-job)) | Model „odwróconej rekrutacji” nie skalował się |
| **SimplyHired** | Zamknięcie i przejęcie przez Recruit w 2016 ([HR Dive, 2016](https://www.hrdive.com/news/simplyhired-may-be-shutting-down-june-26/420078/)) | Konsolidacja wokół Indeed |
| **Facebook Jobs** | Wyłączony poza USA i Kanadą w 2022 | Niska skuteczność, zmiana priorytetów |

### 3.2. Czy Google for Jobs i Indeed wystarczają użytkownikowi?

**[O] Dla ogólnego szukania pracy w Polsce: w dużej mierze tak.** Pracuj.pl, OLX, LinkedIn, Jooble i Google pokrywają większość ofert, a Indeed w Polsce ma marginalny zasięg (366 tys. RU wobec 3,08 mln Pracuj i 3,64 mln GoWork, IV 2026). Ogólny agregator nie wnosi nic, czego nie robią już Jooble i Google.

**Nie wystarczają w niszy studenckiej.** Brakuje:
1. filtrów kluczowych dla studenta: umowa zlecenie i składki ZUS do 26 lat, godziny pogodzone z planem zajęć, staż płatny lub niepłatny, minimalna liczba godzin tygodniowo, dojazd z kampusu;
2. przeliczenia widełek „na rękę” dla studenta;
3. zaufania: weryfikacji pracodawców i flag ryzyka, np. „niepłatny staż dłuższy niż 6 miesięcy” w kontekście przyszłej ustawy;
4. kuracji: zamiast 2000 wyników, 15 najlepszych ofert tygodnia dla studenta SGH lub UW;
5. integracji z życiem uczelni: koła naukowe, biura karier, targi.

To realna, ale **wąska** luka. Część z niej wypełniają JobTeaser (biura karier) i grupy FB.

---

## 4. Rynek i monetyzacja

### 4.1. Wielkość rynku

| Wskaźnik | Wartość | Źródło |
|---|---|---|
| Nowe ogłoszenia na 50 największych portalach w PL | 253 tys. (I 2026), 238 tys. (II 2026), 264,6 tys. (IV 2026), 267,2 tys. (V 2026), 257 tys. (VIII 2026, +4% r/r) | **[F]** Grant Thornton ([I 2026](https://grantthornton.pl/publikacja/oferty-pracy-w-styczniu-2026-rynek-pracy-nadal-w-dolku/); [IV 2026](https://grantthornton.pl/publikacja/oferty-pracy-w-kwietniu-2026-wyrazny-wzrost-dynamiki/); [V 2026](https://grantthornton.pl/wp-content/uploads/2026/06/OFERTY-PRACY-maj-2026-1.pdf); [VIII 2026, Element](https://elementapp.ai/blog/oferty-pracy-polska-sierpien-2026-raport-grant-thornton/)) |
| Wolne miejsca pracy (GUS) | 98,7 tys. na koniec II kw. 2026 | **[F]** [Podatki.biz za GUS, 2026](https://www.podatki.biz/artykuly/gus-niewielki-spadek-liczby-wakatow-w-ujeciu-kwartalnym_16_63601.htm) |
| Przychody Grupy Pracuj | 811,2 mln zł (2025); 425,5 mln zł (H1 2026); cel 1,4 mld zł w 2030 | **[F]** Parkiet 2026; PulsHR 2026 |
| Przychody HR Technology Recruit (Indeed + Glassdoor) | 9,67 mld USD (FY2025) | **[F]** Recruit 2026 |
| Rynek rekrutacji online w Europie | ok. 9,25 mld USD (2025) | **[F, źródło o niskiej wiarygodności]** [Expert Market Research](https://www.expertmarketresearch.com/de/reports/europe-online-recruitment-market) |
| Rynek ogłoszeń rekrutacyjnych online w PL (przychody) | **ok. 1,2–1,6 mld zł/rok** | **[S]** = segment Polska Grupy Pracuj (309,3 mln zł × 2 ≈ 620 mln zł) ÷ założony udział 40–50% |
| Studenci w PL | 1 322,8 tys. (31.12.2025) | **[F]** [GUS, 2026](https://publikacje.new.stat.gov.pl/en/publications-portal/higher-education-20252026-academic-year) |
| Studenci pracujący w trakcie studiów | 80% w PL vs 78% średnio w 26 krajach | **[F]** Eurostudent VIII (dane 2021–2024, raport XII 2024) ([gov.pl](https://www.gov.pl/attachment/73bbbcd8-e89d-4f03-863d-4743d5d677a6); [Bank.pl](https://bank.pl/zapracowany-jak-polski-ucze-i-student/)) |
| Studenci w UE | 18,8 mln (2023) | **[F]** [Eurostat](https://ec.europa.eu/eurostat/statistics-explained/index.php/Tertiary_education_statistics) |

### 4.2. TAM / SAM / SOM

| Poziom | Wariant ogólny (PL) | Wariant niszowy: studenci (PL) | Niszowy: Europa (później) |
|---|---|---|---|
| **TAM** | **[S]** 8–10 mln unikalnych użytkowników serwisów pracy miesięcznie = suma RU top-10 grup (17,0 mln, Gemius IV 2026) × (1 − duplikacja 40–50%). Przychodowo ok. 1,2–1,6 mld zł/rok. | **[S]** 1 322,8 tys. studentów × 80% pracujących ≈ **1,06 mln osób** | **[S]** 18,8 mln × 78% ≈ **14,7 mln** |
| **SAM** | **[S]** Użytkownicy agregatorów i wyszukiwarek: ruch Jooble z PL 4,06 mln wizyt ÷ ok. 2 wizyty na osobę ≈ **1,5–2,5 mln** | **[S]** TAM × 35% aktywnie szukających w danym miesiącu ≈ **370 tys.** | **[S]** 14,7 mln × 35% ≈ 5,1 mln, ale każdy kraj to inny język i inni lokalni gracze |
| **SOM (po 3 latach)** | **[S]** 0,5–2% SAM = **10–50 tys. MAU** | **[S]** 5–15% SAM = **18–55 tys. MAU studentów** + ruch SEO od niestudentów → **60 tys. MAU** w scenariuszu bazowym | Nie wcześniej niż po udowodnieniu modelu w PL |

### 4.3. Modele przychodów: stawki i przychód przy 10 / 100 / 500 tys. MAU

Kwoty w zł miesięcznie, **wariant bazowy (zakres pesymistyczny–optymistyczny)**. Wszystkie stawki to **[S]**, z punktami odniesienia z rynku: mediana CPC płacona przez pracodawców za ogłoszenie w USA 0,92 USD i mediana CPA 19,32 USD (Appcast, 2025; [HR Dive](https://www.hrdive.com/news/cost-per-hire-application-increase-2025-recruitment-appcast/812612/)); w Wielkiej Brytanii CPC i CPA spadały w 2025, a odsetek aplikacji wynosił ok. 5% ([Appcast UK, 2026](https://www.businesswire.com/news/home/20260426166465/en/Appcast-Releases-2026-U.K.-Recruitment-Marketing-Benchmark-Report-as-Labour-Market-Softens-and-Hiring-Costs-Decline)); mediana CPC w wyszukiwarce w Polsce ok. 2,80 zł (2026, [Sempire](https://www.sempire.pl/srednie-stawki-cpc-2026-ile-kosztuje-klikniecie-w-polskim-e-commerce-kompletny-przewodnik-po-branzach.html)); Pracuj.pl 299–599 zł, JJIT od 99 zł za ogłoszenie (2026); RPM AdSense 0,5–15 USD ([Ranktracker](https://www.ranktracker.com/pl/blog/how-much-does-adsense-pay-for-1-000-pageviews/)).

| Model | Wzór i założenia (bazowe) | 10 tys. MAU | 100 tys. MAU | 500 tys. MAU | Zalety | Wady |
|---|---|---|---|---|---|---|
| **CPC afiliacyjny** (feedy Talent.com, Careerjet itd.) | 3 kliknięcia wychodzące na MAU × 40% płatnych × 0,30 zł | 3 600 (900–10 000) | 36 000 (9 000–100 000) | 180 000 (45 000–500 000) | Działa od 1. dnia, zero sprzedaży | Niskie stawki, zależność od partnera, ruch odpływa |
| **CPA** (płatność za aplikację) | 3 × 5% aplikacji × 10% płatnych × 15 zł | 2 250 (500–9 600) | 22 500 (5 000–96 000) | 112 500 (25 000–480 000) | Wyższa wartość jednostkowa | Wymaga umów z pracodawcami i śledzenia aplikacji; częściowo zastępuje CPC |
| **Płatne ogłoszenia** | 1 ogłoszenie na 1000 MAU × 149 zł | 1 490 (495–3 980) | 14 900 (4 950–39 800) | 74 500 (24 750–199 000) | Unikalna treść, Twoja baza | Zimny start, sprzedaż B2B |
| **Promowanie ofert** | 25% ogłoszeń × 79 zł | 198 (37–693) | 1 975 (368–6 930) | 9 875 (1 838–34 650) | Wysoka marża | Wymaga wolumenu |
| **Premium dla kandydatów** | 0,3% × 19 zł | 570 (100–1 920) | 5 700 (999–19 200) | 28 500 (4 995–96 000) | Przychód cykliczny | **[O]** Studenci mało płacą; ryzyko złego PR |
| **Alerty sponsorowane** | 30% MAU zapisanych × 8 wysyłek × 25 zł CPM | 600 (120–1 920) | 6 000 (1 200–19 200) | 30 000 (6 000–96 000) | Alerty budują retencję | Męczy odbiorców |
| **Reklamy display** | 8 odsłon na MAU × 6 zł RPM | 480 (150–1 200) | 4 800 (1 500–12 000) | 24 000 (7 500–60 000) | Prosty | Psuje UX, niskie RPM w PL |
| **Narzędzia dla pracodawców** (mini-ATS, profil, statystyki) | 0,5 klienta na 1000 MAU × 199 zł/mies. | 995 (248–2 990) | 9 950 (2 475–29 900) | 49 750 (12 375–149 500) | Przychód cykliczny | Konkurencja ATS (eRecruiter, Teamtailor) |
| **Dane i raporty płacowe** | Raporty B2B z **własnych** danych | 0 | 1 667 (0–3 333) | 8 333 (1 667–16 667) | Marka ekspercka | Feedy partnerów zwykle zakazują agregacji (np. Adzuna) |
| **Uczelnie i biura karier** | Licencja 6–15 tys. zł/rok × liczba uczelni | 500 (0–1 000) | 4 167 (1 500–8 333) | 18 750 (6 250–37 500) | Dystrybucja + przychód | Długie zakupy publiczne, JobTeaser już obecny |
| **Realistyczny miks** (CPC + ogłoszenia + promowanie + alerty + SaaS + uczelnie) | ARPU 0,69 zł (0,18–1,96 zł) | **≈ 7 400** (1 800–20 600) | **≈ 73 000** (19 500–204 000) | **≈ 363 000** (96 000–1 017 000) | — | — |

**[O]** Przy 10 tys. MAU biznes nie utrzymuje nawet jednej osoby. Sensowny przychód zaczyna się od ok. 100 tys. MAU. Zakres między scenariuszami jest duży, więc pierwsze 2–3 miesiące działania powinny służyć **zmierzeniu** prawdziwej stawki CPC i konwersji.

### 4.4. Model finansowy na 3 lata

Założenia [S]: MAU rośnie liniowo w ciągu roku; przychód = średnie MAU × 12 × ARPU; ARPU rośnie wraz z uruchamianiem sprzedaży do pracodawców i uczelni; w 1. roku założyciel pracuje bez wynagrodzenia (koszt alternatywny pominięty!). Kwoty w zł.

| | **Pesymistyczny** R1 / R2 / R3 | **Bazowy** R1 / R2 / R3 | **Optymistyczny** R1 / R2 / R3 |
|---|---|---|---|
| MAU na koniec roku | 1 500 / 6 000 / 12 000 | 5 000 / 25 000 / 60 000 | 15 000 / 100 000 / 300 000 |
| ARPU (zł/MAU/mies.) | 0,15 / 0,25 / 0,35 | 0,30 / 0,50 / 0,75 | 0,50 / 0,90 / 1,20 |
| **Przychody** | 1 350 / 11 250 / 37 800 | 9 000 / 90 000 / 382 500 | 45 000 / 621 000 / 2 880 000 |
| Infrastruktura | 4 000 / 8 000 / 12 000 | 5 000 / 12 000 / 24 000 | 8 000 / 30 000 / 90 000 |
| Pozyskanie ofert (licencje, feedy) | 0 / 0 / 0 | 0 / 3 000 / 6 000 | 0 / 12 000 / 30 000 |
| Marketing | 6 000 / 12 000 / 15 000 | 10 000 / 40 000 / 90 000 | 25 000 / 150 000 / 450 000 |
| SEO i treści | 0 / 4 000 / 6 000 | 3 000 / 18 000 / 30 000 | 6 000 / 48 000 / 96 000 |
| Prawnik | 5 000 / 2 000 / 2 000 | 8 000 / 4 000 / 6 000 | 10 000 / 12 000 / 20 000 |
| Księgowość i spółka | 0 / 6 000 / 7 200 | 2 000 / 9 600 / 10 800 | 3 000 / 12 000 / 18 000 |
| Narzędzia (SaaS) | 3 000 / 4 000 / 5 000 | 4 000 / 6 000 / 9 000 | 6 000 / 12 000 / 24 000 |
| Ludzie (wynagrodzenia, freelancerzy) | 0 / 0 / 0 | 0 / 48 000 / 156 000 | 0 / 180 000 / 900 000 |
| **Koszty razem** | 18 000 / 36 000 / 47 200 | 32 000 / 140 600 / 331 800 | 58 000 / 456 000 / 1 628 000 |
| **Wynik roczny** | −16 650 / −24 750 / −9 400 | −23 000 / −50 600 / +50 700 | −13 000 / +165 000 / +1 252 000 |
| **Wynik skumulowany** | −50 800 po 3 latach | −22 900 po 3 latach | +1 404 000 po 3 latach |
| MAU potrzebne do progu rentowności | ok. 10–12 tys. | 8,9 tys. / 23,4 tys. / 36,9 tys. | 9,7 tys. / 42,2 tys. / 113 tys. |
| **Trwały miesięczny próg rentowności** | ok. 35. miesiąca (tylko dzięki zerowym kosztom ludzi) | **ok. 29. miesiąca** | ok. 17. miesiąca |

**[O]** Optymistyczny scenariusz wymaga trafienia w kanał wzrostu (np. dominacji w SEO na frazach „staż [miasto]”) i zewnętrznego finansowania w 2. roku. Bazowy to „mały, rentowny serwis niszowy”. Pesymistyczny to sygnał, by po 6–9 miesiącach zrobić pivot.

### 4.5. Koszt pozyskania użytkownika, SEO i efekt sieciowy

- **[F]** CPC reklam na Facebooku: średnio 0,70 USD w kampaniach ruchu (dane z X 2025, [Influee](https://influee.co/pl/blog/how-much-do-facebook-ads-cost)). Średni CPC Google Ads w branży „Employment Services”: 2,04 USD (WordStream 2025, [Focus Digital](https://focus-digital.co/?p=6055)).
- **[S]** Jeśli 25% osób z płatnej reklamy wraca lub zapisuje się na alerty, **CAC wynosi ok. 10 zł (Meta) lub ok. 30 zł (Google Ads)**. Wartość klienta przy ARPU 0,5 zł i 5 miesiącach aktywności to **ok. 2,5 zł**. LTV/CAC = 0,08–0,25, więc **płatne pozyskanie się nie zwraca**. Wzrost musi być organiczny.
- **SEO:** strony typu „staże płatne Warszawa”, „praca dla studenta Mokotów”, „praca na zlecenie student 26 lat”. **[F]** Uwaga: Google karze masowe generowanie stron bez wartości (polityka scaled content abuse; [Google Search Central](https://developers.google.com/search/docs/essentials/spam-policies)). Badania z 2025–2026 pokazują spadek CTR wyników organicznych przy AI Overviews (np. utrata ok. 34,5% kliknięć r/r dla stron z AI Overview, [Visionary Marketing, 2026](https://visionary-marketing.co.uk/blog/ai-overviews-traffic-impact-2026); dla portali pracy: [Recruiting News Network](https://www.recruitingnewsnetwork.com/posts/the-growing-impact-of-ai-overviews-on-recruitment-marketing-and-talent-acquisition)). **[O]** SEO pozostaje kluczowe, ale jest mniej przewidywalne niż 5 lat temu. Retencję trzeba budować własnymi kanałami (e-mail, push, społeczność).
- **Efekt sieciowy [O]:** czysty agregator ma słaby efekt sieciowy, bo oferty są towarem i każdy może je zebrać. Silny efekt pojawia się dopiero, gdy pracodawcy publikują **bezpośrednio u Ciebie**, bo docierasz do studentów, których nie mają gdzie indziej (pętla: studenci → unikalne oferty → studenci). Dlatego od 1. dnia trzeba budować stronę popytu (społeczność studentów) i podaży (bezpośrednie oferty), a feedy traktować tylko jako uzupełnienie na zimny start.

---

## 5. Strategia wejścia i MVP

### 5.1. Nisza czy agregator ogólny?

| Nisza | Popyt | Konkurencja | Dostęp do danych | Monetyzacja | Ocena [O] |
|---|---|---|---|---|---|
| **Studenci: płatne staże i praca (Warszawa → PL)** | Wysoki (80% pracuje) | Średnia: JobTeaser na uczelniach, OLX, Pracuj, grupy FB | 🟢 ATS za zgodą, oferty bezpośrednie, feedy | Pracodawcy płacą za dostęp do studentów; uczelnie | **6/10** (najlepsza) |
| Praca dorywcza i sezonowa | Wysoki | Wysoka: OLX dominuje, FB Local Jobs (USA, możliwa ekspansja) | 🔴 Główne źródła niedostępne | Niska (małe firmy, niskie budżety) | 3/10 |
| Praca zdalna | Średni–wysoki | Globalna: LinkedIn, JJIT, serwisy zagraniczne | 🟢 ATS globalnych firm | Średnia | 4/10 |
| IT | Średni | Bardzo wysoka: JJIT, NFJ + theprotocol (Grupa Pracuj), Bulldogjob | 🔴/🟠 | Wysoka, ale zajęta | 2/10 |
| Sektor publiczny | Średni | ePraca, serwisy ministerstw | 🟢 Dane publiczne (obowiązek zgłaszania od VI 2025) | **Słaba** (instytucje rzadko płacą) | 4/10 (dobra jako projekt SEO) |
| Ogólny agregator | Wysoki | Ekstremalna | 🔴 | Niska | 2/10 |

**[O]** Idź w niszę studencką i zawęź ją jeszcze bardziej na start: **„płatne staże i praca dla studentów kierunków ekonomiczno-biznesowych w Warszawie”** (SGH, UW WNE i WZ, ALK, Koźmiński). Znasz tę grupę, masz do niej dostęp i to ją pracodawcy (Big4, banki, consulting, FMCG, centra usług wspólnych) chcą najbardziej.

### 5.2. Plan MVP (Claude Code + elementy no-code)

**Źródła ofert od 1. dnia (legalnie):**
1. Lista 100–200 firm rekrutujących studentów w Warszawie. Sprawdź, jakiego ATS używają (Greenhouse, Lever, Recruitee, Teamtailor, Workable, SmartRecruiters, eRecruiter). Wyślij im e-mail: „pokazujemy Wasze staże studentom SGH/UW za darmo, z linkiem do Waszej strony; zgoda?”. Pobieraj oferty tylko od firm, które się zgodzą lub przez 14 dni nie zgłoszą sprzeciwu. **[O]** Wariant z brakiem sprzeciwu jest słabszy prawnie, więc lepiej z wyraźną zgodą.
2. Feedy Careerjet lub Talent.com (zarabiasz na kliknięciu) i Adzuna/Jooble z wymaganymi oznaczeniami, filtrowane po słowach „staż”, „praktyka”, „student”, „junior”.
3. Darmowy formularz „Dodaj staż” dla pracodawców (Tally → Supabase) z ręczną moderacją.
4. Rozmowy z biurami karier SGH i UW oraz kołami naukowymi o wymianie ofert.

**Stos [O]:** Next.js (strony SEO z `JobPosting` tylko dla ofert bezpośrednich), Supabase (Postgres + autoryzacja), Meilisearch, GitHub Actions (cron), Resend lub Brevo (alerty), Claude Haiku 4.5 do normalizacji, Plausible lub Umami (analityka zgodna z RODO). Newsletter na start: Substack lub Beehiiv.

**Pierwsi użytkownicy:**
- cotygodniowy newsletter „15 najlepszych płatnych staży tygodnia” (kuracja ręczna + automat);
- posty w grupach roczników, koła naukowe, samorządy, Discord i Instagram;
- 5–10 ambasadorów na uczelniach (np. dostęp premium lub certyfikat zamiast pieniędzy);
- treści SEO i social typu „Ile płacą na stażach w Big4 w 2026” na podstawie **własnej ankiety**, a nie scrapingu.

### 5.3. Test popytu w 4–8 tygodni za prawie 0 zł

| Tydzień | Działanie | Koszt |
|---|---|---|
| 1 | Landing page z obietnicą wartości i zapisem na alerty; 15 wywiadów ze studentami (problem, obecne narzędzia, czego brakuje) | 0–50 zł (domena) |
| 2 | Ręcznie wyselekcjonowane 30–50 ofert (linki do źródeł); 1. wydanie newslettera; dystrybucja w 10–20 grupach i kanałach | 0 zł |
| 3–4 | Automatyzacja pobierania z 2–3 legalnych źródeł; alerty e-mail z filtrami; 20 rozmów z pracodawcami: „czy zapłacisz 99–199 zł za wyróżnienie stażu?” (prośba o list intencyjny lub przedpłatę) | 0–100 zł |
| 5–6 | Fake-door test: przycisk „Premium: przelicznik na rękę + priorytetowe alerty” i pomiar kliknięć; pierwsze płatne wyróżnienie | 0 zł |
| 7–8 | Analiza wskaźników; decyzja: kontynuacja, pivot albo stop | 0 zł |

### 5.4. Kluczowe wskaźniki i warunki pivotu lub rezygnacji

| Wskaźnik (po 6–8 tyg.) | Kontynuuj | Pivot | Stop |
|---|---|---|---|
| Zapisy na alerty / newsletter (organicznie) | ≥ 1 000 | 300–1 000 | < 300 |
| Wskaźnik otwarć newslettera | ≥ 45% | 30–45% | < 30% |
| CTR z newslettera i alertów do ofert | ≥ 10% | 4–10% | < 4% |
| Retencja W4 (użytkownik wraca po 4 tygodniach) | ≥ 25% | 10–25% | < 10% |
| Pracodawcy, którzy zapłacili lub podpisali list intencyjny | ≥ 3 | 1–2 | 0 po 20 rozmowach |
| Stawka CPC z feedów (rzeczywista) | ≥ 0,25 zł | 0,10–0,25 zł | < 0,10 zł |
| Koszt organiczny na zapisanego użytkownika (czas × stawka 30 zł/h) | < 5 zł | 5–15 zł | > 15 zł |

**Kierunki pivotu [O]:** (1) media i społeczność, czyli newsletter oraz Instagram/TikTok o stażach z przychodem ze sponsoringu pracodawców; (2) narzędzie B2B dla kół naukowych i samorządów (tablica ofert z feedów partnerów); (3) „karierowy copilot” dla studentów (CV, przygotowanie do rozmów) z ofertami z feedów partnerskich; (4) własny raport płac stażowych z ankiet jako produkt dla pracodawców.

---

## 6. Werdykt

### 6.1. Osiągalność

| Wymiar | Wariant ogólny | Wariant niszowy (studenci) |
|---|---|---|
| Technicznie | ✅ Tak | ✅ Tak |
| Prawnie | ⚠️ Z zastrzeżeniami, a przy pokryciu dużych portali w praktyce **nie** (bez scrapingu nie ma ofert, ze scrapingiem jest ryzyko sui generis, regulaminów i RODO) | ✅ **Tak**, przy źródłach licencjonowanych, ofertach bezpośrednich i ATS za zgodą |
| Biznesowo | ❌ Bardzo trudne | ⚠️ Z zastrzeżeniami |
| **Szanse powodzenia [O]** | **2/10.** Konkurencja z Jooble, Pracuj, LinkedIn, OLX i Google, brak legalnego dostępu do danych, agregatory upadają lub tną koszty (Joblift, Jooble). | **4/10 jako biznes, 7/10 jako projekt edukacyjny i portfolio.** Luka produktowa jest realna i masz dostęp do grupy docelowej, ale ARPU jest niskie, start bez ofert trudny, a JobTeaser już siedzi na uczelniach. |

### 6.2. Trzy najważniejsze ryzyka

1. **Dostęp do danych i prawo:** brak API do odczytu u gigantów, ochrona sui generis (Innoweb, CV‑Online), skuteczne regulaminy (Ryanair) i RODO (Bisnode, KASPR). Scraping to droga do pozwu lub blokady.
2. **Dystrybucja:** płatne pozyskanie się nie zwraca (CAC 10–30 zł wobec LTV ok. 2,5 zł); ruch z Google maleje przez AI Overviews, a w tle rosną ChatGPT i Indeed z agentami AI.
3. **Monetyzacja i konsolidacja:** niskie ARPU, wolna sprzedaż B2B, Grupa Pracuj konsoliduje rynek (NFJ VII 2026, cel 1,4 mld zł w 2030) i rozwija segmenty pink i blue collar.

### 6.3. Trzy najważniejsze szanse

1. **Niedoobsłużone potrzeby studentów:** zlecenie i ZUS do 26 lat, godziny pod plan zajęć, płatne staże, a od 2027 prawdopodobnie ustawa o stażach z obowiązkowym świadczeniem.
2. **Jawność wynagrodzeń:** od 24.12.2025 pracodawca musi podać wynagrodzenie kandydatowi, a dyrektywa UE wymusi dalsze zmiany. Normalizacja i przeliczanie płac „na rękę” to realna wartość.
3. **Tanie AI i legalne feedy:** normalizacja tysięcy ofert kosztuje dziesiątki dolarów miesięcznie, a feedy partnerskie (Talent.com, Careerjet) płacą za ruch od 1. dnia. Mały zespół może zbudować lepszy UX niż zasiedziali gracze w wąskiej niszy.

### 6.4. Rekomendowany wariant i alternatywy

**Rekomendacja [O]:** *„Płatne staże i praca dla studentów w Warszawie”*, zbudowane wokół **newslettera i alertów** (retencja), **ofert bezpośrednich i ATS za zgodą** (unikalność, legalność) oraz **feedów partnerskich** (zapełnienie bazy i przychód CPC). Zero scrapingu dużych portali. Budżet startowy: kilkaset złotych plus konsultacja prawna przed pierwszą fakturą.

**Alternatywy o lepszym stosunku szans do ryzyka [O]:**

| Alternatywa | Dlaczego lepsza | Ryzyko |
|---|---|---|
| **Media i społeczność o stażach** (newsletter + Instagram/TikTok + raporty płac z własnych ankiet) | Nie potrzebuje bazy ofert; przychód ze sponsoringu pracodawców; łatwy test | Zależność od jednego założyciela |
| **Narzędzie dla kół naukowych i organizacji studenckich** (tablica ofert, CRM partnerów) | Klienci są blisko; mały, ale realny przychód B2B | Małe budżety |
| **„Karierowy copilot” dla studentów** (CV, rozmowy, dopasowanie do ofert z feedów) | Wyższa skłonność do płacenia za konkretny efekt; feedy legalne | AI Act (rekomendacje), konkurencja ze strony ChatGPT i Indeed |
| **Agregator ofert sektora publicznego** (ePraca, nabory administracji) | Dane publiczne, nieduża konkurencja w UX | Słaba monetyzacja; dobry projekt SEO lub portfolio |

---

## Załącznik A. Lista kontrolna weryfikacji każdego źródła (przed integracją)

1. Czy istnieje oficjalne API lub feed? Zapisz link do dokumentacji i datę.
2. Czy warunki pozwalają na **wyświetlanie publiczne** i **użycie komercyjne**? Jakie oznaczenia (np. „Jobs by Adzuna”)? Czy wolno przechowywać dane (cache) i jak długo?
3. Czy warunki zakazują agregacji lub statystyk (np. średnich płac)?
4. Co mówi regulamin strony o robotach i kopiowaniu? Zrób zrzut ekranu z datą.
5. Czy dane zawierają informacje osobowe? Jak je usuniesz?
6. Czy masz zgodę pracodawcy (e-mail lub umowa) w przypadku ATS i stron kariery?
7. `robots.txt` i limity zapytań: ustaw je w konektorze.
8. Procedura usunięcia źródła na żądanie (wyłącznik konektora + czyszczenie danych).

## Załącznik B. Pytania do prawnika (IP + RODO)

1. Czy wyświetlanie ofert z feedów partnerów (Careerjet, Talent.com, Adzuna, Jooble) w moim interfejsie jest zgodne z ich warunkami i nie narusza praw osób trzecich?
2. Czy pobieranie ofert z publicznych endpointów ATS za zgodą pracodawcy (e-mail) jest wystarczające? Jak sformułować zgodę?
3. Czy moja baza ofert bezpośrednich jest chroniona sui generis i jak to wykorzystać w regulaminie?
4. Test równowagi (art. 6 ust. 1 lit. f) dla danych firmowych w ofertach oraz obowiązek z art. 14 RODO: czy da się go uniknąć, nie przetwarzając danych osób?
5. Regulamin DSA (mikroprzedsiębiorstwo), P2B, prawa konsumenta przy premium.
6. AI Act: czy planowane rekomendacje ofert to „ukierunkowane ogłoszenia o pracę” z załącznika III?
7. Forma prawna i odpowiedzialność: działalność nierejestrowana czy spółka z o.o.

## Załącznik C. Wybrane źródła (pełna lista linków jest w tekście)

- Dane rynkowe: [Grupa Pracuj: wyniki 2025](https://ir.grupapracuj.pl/media/792/download/Komunikat_prasowy_Grupa_Pracuj_podsumowuje_wyniki_za_2025_rok.pdf?inline=1) · [Grant Thornton: oferty pracy](https://grantthornton.pl/publikacja/oferty-pracy-w-styczniu-2026-rynek-pracy-nadal-w-dolku/) · [Gemius IV 2026 (GoWork)](https://www.gowork.pl/blog/?p=67777) · [GUS: szkolnictwo wyższe 2025/26](https://publikacje.new.stat.gov.pl/en/publications-portal/higher-education-20252026-academic-year) · [Recruit FY2025](https://file.recruit-holdings.com/files/en/Recruit_202603Q4_summary_en.pdf) · [LinkedIn FY2026](https://news.linkedin.com/2026/q4-earnings-and-business-highlights)
- Dostęp do danych: [Adzuna API ToS](https://developer.adzuna.com/docs/terms_of_service) · [Jooble API](https://jooble.org/api/about) · [Talent.com Publishers](https://employers.talent.com/publishers) · [Careerjet API](https://github.com/careerjet/careerjet-api-client-python) · [Google JobPosting](https://developers.google.com/search/docs/appearance/structured-data/job-posting) · [Meta Graph API v19](https://developers.facebook.com/docs/graph-api/changelog/version19.0/)
- Prawo: [ustawa o ochronie baz danych](https://eli.gov.pl/eli/DU/2024/1769/ogl/pol/pdf) · [CV‑Online Latvia (TSUE 2021)](https://www.ippt.eu/sites/ippt/files/2021/IPPT20210603_CJEU_CV-Online_Latvia_v_Melons.pdf) · [Innoweb (TSUE 2013)](https://www.scl.org/2984-database-right-innoweb-v-wegener-cjeu-judgment/) · [Ryanair v PR Aviation (TSUE 2015)](https://www.pinsentmasons.com/out-law/news/website-operators-can-prohibit-screen-scraping-of-unprotected-data-via-terms-and-conditions-says-eu-court-in-ryanair-case) · [CNIL KASPR (2024)](https://www.cnil.fr/en/data-scraping-kaspr-fined-eu240000) · [AI Act Annex III](https://artificialintelligenceact.eu/annex/3/) · [AI Omnibus (FPF 2026)](https://fpf.org/blog/the-ai-act-implementation-timeline-what-changes-under-the-ai-omnibus/)
