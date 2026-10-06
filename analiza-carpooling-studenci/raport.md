# Carpooling tylko dla studentów w Polsce — analiza rynku i opłacalności

*Stan na 6 października 2026 r. Model liczbowy z formułami do edycji: [`model-carpooling-studenci.xlsx`](model-carpooling-studenci.xlsx).*

---

## Podsumowanie (TL;DR)

1. **Problem istnieje:** w roku akademickim 2025/26 w Polsce studiowało 1 322 841 osób (GUS, 2026). Około połowa nie mieszka z rodzicami (Eurostudent VIII). Studenci i doktoranci odbyli w 2025 r. 13,7 mln przejazdów samym PKP Intercity.
2. **Głównym konkurentem nie jest BlaBlaCar, tylko pociąg z ulgą 51%.** Na trasie Warszawa–Lublin student płaci ok. 25 zł za IC, który jedzie od 1 h 52 min. Sam koszt paliwa na osobę w aucie z 4 osobami to ok. 19 zł (październik 2026).
3. Przy tak niskich cenach **zostaje bardzo mało miejsca na prowizję**. 12% od 30 zł to 3,60 zł, a po opłacie operatora płatności (1,5% + 1 zł) zostaje ok. 2,10 zł na rezerwację.
4. **Sufit rynku jest niski.** Szacuję, że nawet przy 100% udziale w całym osiągalnym rynku studenckim (SAM ≈ 127 tys. osób) prowizja dałaby ok. 4,4 mln zł brutto rocznie. Realny udział to ułamek tej kwoty.
5. **Kierowców jest za mało.** W BlaBlaCar w Polsce ok. 81,5% kierowców to mężczyźni, a według CBOS (2018) tylko ok. 21% uczniów i studentów miało samochód. Studencka sieć to podzbiór sieci BlaBlaCar (ok. 6 mln aktywnych użytkowników w PL), więc ma mniej ofert, a nie więcej.
6. Historia branży nie zachęca. Zimride, studencki carpooling z USA, zdobył 20% studentów Cornella w pół roku, ale założyciele przeszli na Lyfta, a Zimride zawiesił działalność w 2020 r. Waze Carpool zamknięto w 2022 r., a polski YanosikTLS nie przebił się mimo braku opłat.
7. **Przewagi zawężenia do studentów są realne, ale wąskie:** zaufanie (weryfikacja przez uczelnię), stałe ekipy na piątek i niedzielę, przewóz bagażu na początku i końcu semestru, lokalne grupy, z których studenci już korzystają.
8. W moim modelu bazowym 3 lata dają łącznie ok. **−0,59 mln zł**. W wariancie z płaconym zespołem próg rentowności to ok. 16–29 tys. aktywnych użytkowników, czyli 13–23% całego krajowego SAM. Bez wynagrodzeń (projekt po godzinach) koszty pokrywa ok. 2,5–4,5 tys. aktywnych użytkowników.
9. **Ocena szans na rentowny samodzielny biznes: 3/10.**
10. **Werdykt: warto z zastrzeżeniami.** Warto zrobić tani (≤ 500 zł) test na jednej trasie Warszawa ↔ Lublin w ciągu 6–8 tygodni, z jasnymi kryteriami przerwania. Nie warto inwestować w pełną aplikację, zanim test nie pokaże popytu i podaży kierowców.

---

## Nota metodologiczna

- **FAKT** oznacza liczbę ze źródłem (link w tekście, pełna lista na końcu). **SZACUNEK** to moje założenie: podaję jego uzasadnienie, a w arkuszu można go zmienić.
- Proxy sieciowe w środowisku, w którym robiłem analizę, blokowało część stron (m.in. stat.gov.pl, bankier.pl, antyweb.pl). Część faktów pochodzi więc z treści zindeksowanych przez wyszukiwarkę, a nie z samodzielnie otwartego dokumentu. Kluczowe liczby (GUS, PKP IC, BlaBlaCar) sprawdziłem w kilku niezależnych źródłach. Pojedyncze dane bez potwierdzenia oznaczam „(niepotwierdzone)”.
- Nie znalazłem publicznych danych o tym, **jak często studenci jeżdżą do domu**, ani o liczbie członków grup przejazdowych na Facebooku. To największa luka w danych i pierwsze pytanie do ankiety.

---

## 1. Jak działa BlaBlaCar i podobne firmy

### 1.1 Model biznesowy BlaBlaCar

| Element | Jak działa | Źródło |
|---|---|---|
| Zasada | Kierowca jedzie we własnym celu i dzieli koszty (paliwo, autostrada) z pasażerami. Cena ma odpowiadać kosztom, a nie przynosić zysk. | [bankier.pl](https://www.bankier.pl/wiadomosc/BlaBlaCar-tani-sposob-podrozowania-7530851.html), [regulamin](https://legal.blablacar.com/pl-pl/terms-and-conditions/) |
| Opłata serwisowa (główny przychód) | Płaci pasażer przy rezerwacji. We Francji: część stała 0,89 € + 9,9% + VAT, w praktyce zwykle 16–22% ceny miejsca. | [24matins.fr](https://www.24matins.fr/blablacar-profite-t-il-des-greves-sncf-avec-des-commissions-atteignant-22-par-trajet-1389902), [moneyvox.fr](https://www.moneyvox.fr/votre-argent/actualites/76278/blablacar-un-bon-plan-pour-boucler-ses-fins-de-mois) |
| Płatność w aplikacji | We Francji od 2011 r., w Hiszpanii od 2014 r. Po jej wprowadzeniu społeczność we Francji urosła 5-krotnie, a liczba odwołanych przejazdów mocno spadła. | [economyup.it](https://www.economyup.it/startup/blablacar-ora-il-passaggio-in-auto-si-paga-online-e-scoppiano-le-polemiche/) |
| W Polsce | Pieniądze pasażera trafiają na rachunek u operatora płatności (Hyperwallet), a kierowca dostaje kwotę pomniejszoną o opłatę serwisową. | [regulamin BlaBlaCar PL](https://legal.blablacar.com/pl-pl/terms-and-conditions/) |
| Subskrypcje | BlaBlaPass w Polsce (ok. 2017): 1 zł za 6 miesięcy rezerwacji bez opłat w promocji startowej. Był to etap przejściowy. | [wirtualnemedia.pl](https://www.wirtualnemedia.pl/m/artykul/blablacar-oplata-za-rezerwacje-wycofana-teraz-blablapass), [nowymarketing.pl](https://nowymarketing.pl/blablacar-rezygnuje-z-oplat-serwisowych-i-wprowadza-nielimitowany-blablapass-za-zlotowke/) |
| Inne źródła | Autobusy (BlaBlaCar Bus, po przejęciu Ouibus od SNCF w 2019), sprzedaż biletów innych przewoźników, a w 2025 r. integracja biletów kolejowych we Francji i Hiszpanii (niepotwierdzone w źródle pierwotnym). | [newmobility.news](https://newmobility.news/en/2026/04/22/blablacar-is-shutting-down-its-bus-division-in-france/) |
| Reklamy | Nie są istotnym źródłem przychodu. Nie znalazłem danych. | — |

**Monetyzacja w Polsce — trzy podejścia:**

| Rok | Co zrobił BlaBlaCar w PL | Efekt | Źródło |
|---|---|---|---|
| 2012 (październik) | Start w Polsce | Na głównych trasach kilkaset miejsc, ponad 1 mln wejść miesięcznie (wczesne lata) | [antyweb.pl](https://antyweb.pl/10-pytan-do-michala-pawelca-z-blablacar-pl) |
| 9.03.2016 | Opłata za rezerwację dla pasażerów: (3 zł netto + 12% ceny) × 1,23 VAT, np. przejazd za 15 zł → 3 zł opłaty, za 115 zł → 20 zł. Średnio ok. 20% ceny. | Gniew stałych pasażerów, ucieczka do grup FB. Yanosik uruchomił darmową konkurencję (YanosikTLS). | [bankier.pl](https://www.bankier.pl/wiadomosc/BlaBlaCar-wprowadza-oplaty-za-przejazdy-Rozwoj-kosztuje-7336289.html), [forsal.pl](https://forsal.pl/artykuly/926553,oplata-za-rejestracje-w-blablacar-prowizja-od-rejestracji-blablacar.html), [rp.pl](https://www.rp.pl/transport/art3521781-yanosik-rzuca-wyzwanie-blablacar) |
| ok. 2017 | Wycofanie opłat i wprowadzenie BlaBlaPass | BlaBlaCar tłumaczył to skomplikowaną komunikacją | [wirtualnemedia.pl](https://www.wirtualnemedia.pl/m/artykul/blablacar-oplata-za-rezerwacje-wycofana-teraz-blablapass) |
| później (dokładna data niepotwierdzona) | Powrót opłat serwisowych: np. 55 zł → 7 zł, 77 zł → 10 zł (ok. 13%). Płatność BLIK lub kartą. | Model działa do dziś | [antyweb.pl](https://antyweb.pl/oplata-serwisowa-blablacar) |

**Lekcja dla Ciebie:** polscy użytkownicy carpoolingu są bardzo wrażliwi na opłaty i mają darmową alternatywę (grupy na FB). BlaBlaCar ze swoją skalą musiał się z opłat raz wycofać.

### 1.2 Jak BlaBlaCar rozwiązał problem „kury i jajka” i jak skalował

- **Start od jednego kraju i długich tras.** Covoiturage.fr (2006) przez lata budował płynność we Francji, a dopiero potem rebranding i ekspansja ([TechCrunch, 2014](https://techcrunch.com/2014/10/21/blablacars-ceo-shares-the-companys-10-year-journey-and-global-expansion-plans)). Na długich trasach jedno ogłoszenie kierowcy obsługuje kilka osób, a przejazdy planuje się z wyprzedzeniem, więc dopasowanie jest łatwiejsze niż w dojazdach miejskich.
- **Płatność z góry jako narzędzie płynności, nie tylko przychodu.** Mniej przejazdów odwołanych w ostatniej chwili oznacza więcej zaufania i więcej kierowców (economyup.it, jw.).
- **Kupowanie płynności.** W 2015 r. przejęcia lokalnych liderów: Carpooling.com (Niemcy), AutoHop (Węgry), Podorożniki (Rosja/Ukraina) ([antyweb.pl](https://antyweb.pl/blablacar-przejmuje-niemiecki-carpooling-i-wegierski-autohop), [eu-startups.com](https://www.eu-startups.com/2015/03/blablacar-acqui-hired-budapest-based-autohop-to-expand-in-the-region/), [antyweb.pl](https://antyweb.pl/blablacar-idzie-na-wschod-przejmuje-podorozhniki-korzystacie-z-tego-typu-serwisow)). W Polsce, według moich ustaleń, BlaBlaCar rósł organicznie od 2012 r.
- **Kapitał.** Przez lata firma była nierentowna. Rentowność ogłosiła dopiero w 2024 r. (zysk od ok. kwietnia 2022, dodatnia EBITDA za 2023) ([BlaBlaCar newsroom](https://newsroom.blablacar.com/news/blablacar-closes-financing-round-to-fuel-its-growth-ambitions), [TechCrunch, 2024](https://techcrunch.com/2024/04/02/after-reaching-profitability-carpooling-platform-blablacar-secures-108-million-debt-line)). To 16–18 lat od startu.

### 1.3 Zaufanie i bezpieczeństwo

| Mechanizm | Opis | Źródło |
|---|---|---|
| Profile zweryfikowane | Potwierdzenie danych i dokumentu tożsamości daje niebieską odznakę | [antyweb.pl](https://antyweb.pl/super-driver-blablacar) |
| Oceny i odznaka „Super Driver” | Dla dobrze ocenianych kierowców z niskim odsetkiem odwołań | jw. |
| Ubezpieczenie | We Francji AXA oferuje kierowcom ochronę za 2 € za przejazd (udział własny do 1 500 €, holowanie, gwarancja dotarcia pasażerów). Nie znalazłem odpowiednika dla Polski. | [AXA](https://axa.com/press/press-releases/blablacar-insurance-ridesharing) |
| Oszustwa | CERT Polska ostrzegał przed fałszywymi ogłoszeniami i linkami do fałszywych płatności podszywających się pod BlaBlaCar | [android.com.pl](https://android.com.pl/news/390469-korzystasz-z-blablacar-uwazaj-na-nowe-oszustwo/) |

### 1.4 Kluczowe wskaźniki BlaBlaCar

| Wskaźnik | Wartość | Rok | Źródło |
|---|---|---|---|
| Przychody grupy | 253 mln € (+29% r/r) | 2023 | [BlaBlaCar newsroom](https://newsroom.blablacar.com/news/blablacar-closes-financing-round-to-fuel-its-growth-ambitions), [usine-digitale.fr](https://www.usine-digitale.fr/article/12-ans-apres-sa-creation-blablacar-devienttteint-enfin-la-rentabilite.N746344) |
| Rentowność | Dodatnia EBITDA za 2023; zysk od ok. 04.2022 | 2022–2023 | jw. |
| Pasażerowie (auto + bus) | 80 mln (+23% r/r) | 2023 | jw. |
| Kraje | 21 | 2024 | [TechCrunch](https://techcrunch.com/2024/04/02/after-reaching-profitability-carpooling-platform-blablacar-secures-108-million-debt-line) |
| Finansowanie | Linia kredytowa 100 mln € | 04.2024 | jw. |
| Polska: aktywni użytkownicy | ok. 6 mln (dane firmy); kierowcy zadeklarowali gotowość zabrania 4 mln pasażerów w 2023 r. | 2023 | [antyweb.pl](https://antyweb.pl/blablacar-wyniki-2023) |
| Polska: płeć kierowców | 81,5% to mężczyźni, wśród pasażerów przeważają kobiety (niepotwierdzone w źródle pierwotnym) | b.d. | wyniki wyszukiwania |
| BlaBlaCar Bus | ponad 6 mln pasażerów na 400 liniach. W kwietniu 2026 ogłoszono, że do końca 2026 r. BlaBlaCar przestaje być przewoźnikiem autobusowym we Francji (trwałe straty; 40 z 800 etatów). | 2025–2026 | [newmobility.news](https://newmobility.news/en/2026/04/22/blablacar-is-shutting-down-its-bus-division-in-france/), [european.express](https://www.european.express/2026/04/21/blablacar-ceases-its-activity-as-a-bus-operator-in-france/) |
| Indie | Szacunkowo 20 mln pasażerów w 2025 r., największy rynek firmy | 2025 | [channeliam.com](https://en.channeliam.com/2025/11/02/blablacar-india-carpooling-boom/) |
| Średnia prowizja | PL ok. 13% (przykłady), FR 16–22% | różne | zob. 1.1 |
| Koszt pozyskania użytkownika (CAC) | **Niepubliczny**, nie znalazłem danych | — | — |
| Przychody za 2024–2025 | Nie znalazłem wiarygodnych oficjalnych danych. Serwisy typu „business model canvas” podają liczby bez źródeł, więc ich nie używam. | — | — |

### 1.5 Porównanie z innymi modelami

| Firma | Model | Los | Lekcja dla Ciebie |
|---|---|---|---|
| **Zimride** (USA, 2007) | Carpooling międzymiastowy w **zamkniętych sieciach uczelni i firm**, licencje dla instytucji. Na Cornellu 20% studentów w 6 miesięcy. | Założyciele przeszli na Lyfta (2012–13), Zimride sprzedano Enterprise (2013) i zawieszono 31.12.2020 | **Najbliższy analog.** Studencka sieć daje szybką adopcję na kampusie, ale słaby biznes: sezonowość, mała skala, wolny wzrost konsumencki. [Wikipedia](https://en.wikipedia.org/wiki/Zimride), [CNN](https://cnn.com/interactive/2019/03/business/lyft-history) |
| **Poparide** (Kanada, 2010) | Międzymiastowy carpooling, ok. 2 mln członków. Opłata dla pasażera 4→5 CAD (ok. 20% wartości), limit ceny kierowcy 12 centów/km (niepotwierdzone). | Działa | Limit ceny za km chroni przed „ukrytą taksówką”. [App Store](https://apps.apple.com/app/poparide/id1045332129) |
| „**Poparpool**” | **Nie znalazłem takiej firmy.** Prawdopodobnie chodzi o Poparide. | — | — |
| **Uber Pool / UberX Share** | Współdzielenie kursu w mieście (ride-hailing) | Zawieszony 03.2020, wznowiony 06.2022 jako UberX Share w 9 miastach USA (do 20% zniżki) | Inny rynek (zarobkowy przewóz z licencją). [CNN](https://edition.cnn.com/2022/06/21/tech/uber-restarting-shared-rides) |
| **Hitch** (USA) | Współdzielone kursy w mieście | Przejęty przez Lyft w 10.2014 | Małe platformy są przejmowane albo umierają. [Fortune](https://fortune.com/2014/10/15/hitch-lyft-acquisition) |
| **Scoop** (USA) | Carpooling do pracy przez pracodawców (B2B) | 60 mln USD w 2019, dwie fale zwolnień w 2020 (92 + ponad 40 osób) | Model B2B zależny od jednego wzorca dojazdów. [layoffs.fyi](https://layoffs.fyi/2020/12/02/scoop-conducts-second-layoff-of-2020/) |
| **Waze Carpool** (Google) | Dojazdy do pracy | Zamknięty 09.2022 po pracy zdalnej i zmianie wzorców dojazdów | Nawet Google nie utrzymał płynności przy niestabilnym popycie. [9to5google](https://9to5google.com/2022/08/25/waze-carpool-shut-down/) |
| **FlixBus** | Platforma autobusowa. Linie obsługują lokalni przewoźnicy, a FlixBus zajmuje się marką, sprzedażą i cenami. | Przejął PolskiBus (sprzedaż 12.2017, koniec marki 02.2018) | Autobusy są substytutem, ale bez ulgi studenckiej. [Wikipedia](https://en.wikipedia.org/wiki/PolskiBus) |
| **PKP Intercity** | Kolej. 89,2 mln pasażerów w 2025 (+14%), w tym 13,7 mln przejazdów studentów i doktorantów (+17%). | Rekordy | **Najsilniejszy konkurent dla studentów.** [PKP IC](https://www.intercity.pl/pl/site/o-nas/dzial-prasowy/aktualnosci/pkp-intercity:-podroze-koleja-w-2025-roku.html), [podatki.biz](https://www.podatki.biz/artykuly/pkp-intercity-podsumowuje-rok-2025_16_61090.htm) |
| Sindbad | Przewoźnik autobusowy | Nie znalazłem wiarygodnych aktualnych danych o ofercie krajowej, więc go pomijam | — |

---

## 2. Konkurencja i substytuty w Polsce

### 2.1 Konkurencja bezpośrednia

| Gracz | Opis | Status / wnioski |
|---|---|---|
| **BlaBlaCar** | Lider. Ok. 6 mln aktywnych użytkowników w PL (2023). Opłata serwisowa ok. 13%. | Ma płynność na trasach studenckich. Twoja sieć byłaby jego podzbiorem. |
| **Grupy na Facebooku** (ogólne i dla konkretnych tras) | Darmowe, bez weryfikacji, bez płatności. Rozproszenie: agregator „Podróż Grupowa” skanował ok. 300 takich grup. | Działają „wystarczająco dobrze” i są darmowe. To Twój realny konkurent cenowy. [antyweb.pl](https://antyweb.pl/oferty-wspolnych-przejazdow-na-facebooku), [mamstartup.pl](https://mamstartup.pl/startupy/podroz-grupowa/) |
| **YanosikTLS** („Tanie Linie Samochodowe”, 2016) | Darmowa alternatywa po wprowadzeniu opłat przez BlaBlaCar | Brak śladów skali. Nie udało się ustalić daty zamknięcia. **Lekcja: „za darmo” nie wystarczy, by przebić efekt sieciowy.** [rp.pl](https://www.rp.pl/transport/art3521781-yanosik-rzuca-wyzwanie-blablacar) |
| **otodojazd.pl** + Politechnika Wrocławska | Giełda przejazdów stworzona przez absolwenta PWr. PWr jako pierwsza uczelnia publiczna wdrożyła platformę carpoolingową dla studentów i pracowników. | Precedens współpracy z uczelnią. Nie znalazłem danych o skali. [wroclaw.pl](https://www.wroclaw.pl/otodojazdpl), [tuwroclaw.com](https://www.tuwroclaw.com/wiadomosci,nie-woz-powietrza-politechnika-wroclawska-wdraza-wspolne-dojazdy-dla-studentow-i-pracownikow,wia5-3277-24828.html) |
| Inne (ByTheWay.pl, JedziemyRazem.pl, inOneCar, juntoapp.pl, LocoRide, Carpooling.pl) | Głównie dojazdy do pracy lub uczelni, często darmowe | Brak danych o skali. Rynek jest pełen małych, martwych lub uśpionych serwisów. |
| Grupy uczelniane / samorządowe | Ad hoc na Messengerze i Discordzie | Brak danych |

### 2.2 Substytuty

| Substytut | Fakty | Dla studenta |
|---|---|---|
| **Pociąg** (PKP IC, regionalne) | Ustawowa ulga 51% dla studentów do 26 lat (doktoranci do 35) w 2 kl. TLK/IC/EIC/EIP i u przewoźników regionalnych. Wystarczy mLegitymacja. | Najtańsza i coraz szybsza opcja. 14.10.2025 (Dzień Edukacji Narodowej, przejazd za 1 zł) skorzystało 315 tys. młodych. [PKP IC – ulgi](https://www.intercity.pl/pl/site/dla-pasazera/kup-bilet/przepisy-i-taryfy/ulgi/ulgi-ustawowe/), [PKP IC – rekord](https://www.intercity.pl/pl/site/o-nas/dzial-prasowy/aktualnosci/rekord-liczby-pasazerow-pkp-intercity-w-dzien-edukacji-narodowej.html) |
| **FlixBus** | Ceny dynamiczne od kilku euro. Ulga ustawowa obejmuje według mojej wiedzy autobusową komunikację zwykłą i przyspieszoną, więc FlixBus jej nie stosuje (do weryfikacji). | Tani przy zakupie z wyprzedzeniem, drogi w szczycie |
| **Busy/PKS** | Lokalni przewoźnicy, część z ulgą | Brak spójnych danych |
| **Własne auto** | Pb95: cena maksymalna 6,79 zł/l w programie CPN na 6.10.2026 ([tvp.info](https://www.tvp.info/95762118/cena-paliwa-wtorek-6-pazdziernika-2026-benzyna-95-benzyna-98-diesel), [interia.pl](https://motoryzacja.interia.pl/wiadomosci/news-zmiana-cen-paliw-minister-podal-maksymalne-stawki-na-6-pazdz,nId,23553745)) | Drogo w pojedynkę, więc kierowca ma motywację do zabrania pasażerów |

### 2.3 Porównanie tras

| Trasa | Pociąg: najszybszy czas | Pociąg normalny 2 kl. (od) | **Pociąg student −51%** | FlixBus | BlaBlaCar (SZACUNEK) | Paliwo / auto (SZAC.) | Paliwo / os. przy 4 os. |
|---|---|---|---|---|---|---|---|
| **Warszawa–Lublin** (~170 km) | **1 h 52 min** (IC, po modernizacji linii 7; do 2 h 40) | 51–54 zł | **~25–26 zł** | ~1 h 55–2 h 35, od 5,99 € | 25–35 zł + opłata | ~75 zł | **~19 zł** |
| **Kraków–Rzeszów** (~165 km) | **1 h 14–1 h 19** (EIP / IC Przemyślanin) | IC od 55 zł (EIP od 105 zł) | **~27 zł** | ~2 h, od 9,48 USD | 25–35 zł + opłata | ~73 zł | **~18 zł** |
| **Wrocław–Opole** (~95 km) | **38 min** (EC) | EC/TLK/IC od 33 zł, regionalne taniej | **~16 zł** (IC) | ~1 h 15, od 3,49 € | 15–20 zł + opłata | ~42 zł | **~10 zł** |

Źródła: [jawnylublin.pl](https://jawnylublin.pl/pkp-intercity-majstruje-przy-pociagach-lublin-warszawa-drogie-eic-zamiast-tanszych-ic/), [europodroze.pl W-L](https://www.europodroze.pl/rozklad-jazdy/lublin/warszawa), [europodroze.pl K-R](https://www.europodroze.pl/rozklad-jazdy/rzeszow/krakow), [europodroze.pl W-O](https://www.europodroze.pl/rozklad-jazdy/wroclaw/opole), [FlixBus W-L](https://global.flixbus.com/bus-routes/bus-warsaw-lublin), [FlixBus K-R](https://www.flixbus.com/bus-routes/bus-krakow-rzeszow), [FlixBus W-O](https://global.flixbus.com/bus-routes/bus-wroclaw-opole). Szacunek BlaBlaCar przeskalowałem z danych [antyweb.pl](https://antyweb.pl/koszt-wyjazdu-na-swieta) (Warszawa–Kraków: 30–50 zł, średnio 40 zł). Paliwo liczę przy założeniu 6,5 l/100 km. Dystanse drogowe są przybliżone.

**Wnioski z tabeli:**
- Na trasach ~170 km cena pociągu dla studenta (~25–27 zł) jest **sufitem** dla ceny przejazdu autem. Kierowca z 3 pasażerami po ~22 zł dostaje ~66 zł, czyli mniej więcej zwrot za paliwo. Na prowizję zostaje bardzo mało.
- Na krótkich trasach z dobrą koleją (Wrocław–Opole, 38 min) **carpooling praktycznie nie ma sensu**.
- Auto wygrywa tam, gdzie pociąg jest słaby (brak bezpośredniego połączenia, przesiadki, dom na wsi daleko od stacji), przy bagażu (przeprowadzki na początku i końcu semestru, „słoiki”) i przy podróży od drzwi do drzwi.

### 2.4 Czy BlaBlaCar rozwiązuje Twój problem i gdzie jest luka?

**W dużej mierze rozwiązuje.** Na trasie Warszawa–Lublin BlaBlaCar ma oferty. Twój problem („nie mam z kim wracać”) jest w praktyce problemem **zaufania i preferencji społecznych**, a nie braku przejazdów.

**Możliwe luki (do sprawdzenia w teście):**
1. **Zaufanie / „jadę z kimś z mojej uczelni”.** Weryfikacja e-mailem uczelnianym jest szczególnie ważna dla pasażerek: 81,5% kierowców BlaBlaCar w PL to mężczyźni (niepotwierdzone).
2. **Przejazdy cykliczne („stała ekipa co piątek o 16:00”).** BlaBlaCar jest zoptymalizowany pod jednorazowe rezerwacje.
3. **Brak opłat lub niższe opłaty niż BlaBlaCar.** To jednak oznacza brak przychodu, więc trudno to nazwać luką biznesową.
4. **Szczyty sezonowe i bagaż.** Przeprowadzki w październiku i czerwcu, święta.
5. **Wydarzenia** (juwenalia, festiwale, wyjazdy kół naukowych).

---

## 3. Wielkość rynku (TAM / SAM / SOM)

### 3.1 Fakty wejściowe

| Dana | Wartość | Rok | Źródło |
|---|---|---|---|
| Studenci w Polsce | **1 322 841** (+3,3% r/r) | 2025/26 | GUS, publ. 15.06.2026 ([stat.gov.pl](https://stat.gov.pl/obszary-tematyczne/edukacja/edukacja/szkolnictwo-wyzsze-w-roku-akademickim-20252026,8,12.html), [prawo.pl](https://www.prawo.pl/szkoly-i-uczelnie/liczba-studentow-w-polsce-w-roku-akademickim-2025-26-gus,1546639.html)) |
| w tym stacjonarni / niestacjonarni | ~818 tys. (~62%) / ~505 tys. | 2025/26 | jw. |
| Mazowieckie | 287 763 (21,75%). Mazowieckie, małopolskie, dolnośląskie i wielkopolskie razem mają 54,69% studentów. | 2025/26 | [isr.info.pl](https://www.isr.info.pl/studenci-lgna-do-czterech-wojewodztw/) |
| Miasta | Warszawa ~257 tys., Kraków ~138 tys., Wrocław ~116 tys., Poznań >100 tys., Trójmiasto ~77 tys. | 2024/25 | [Knight Frank](https://content.knightfrank.com/research/2849/documents/pl/prywatne-akademiki-w-polsce-2025-12323.pdf) |
| Lublin | 58 196 (uczelnie w Lublinie) | 2022/23 | [US Lublin](https://lublin.stat.gov.pl/opracowania-biezace/opracowania-sygnalne/edukacja/szkolnictwo-wyzsze-w-wojewodztwie-lubelskim-w-roku-akademickim-20222023,1,9.html?pdf=1) |
| Cudzoziemcy | 108,6 tys. | 2024/25 | [bankier.pl](https://www.bankier.pl/wiadomosc/Ponad-1-28-mln-studentow-w-Polsce-kobiety-wciaz-przewazaja-9032593.html) |
| Mieszkający z rodzicami | ok. połowa (Eurostudent VIII). CBRE: 41% w domu rodzinnym, 11% w akademikach, ~połowa wynajmuje. | 2022–2024 | [PBS](https://pbs.pl/jak-sie-zyje-i-studiuje-w-polsce-eurostudent-viii/), [CBRE](https://biuroprasowe.cbre.pl/97638-w-akademikach-mieszka-co-dziesiaty-student-powod-jest-prosty-tyle-jest-miejsc) |
| Posiadanie samochodu | 21% uczniów i studentów (niepotwierdzone w oryginale) | 2018 | [CBOS](https://www.cbos.pl/SPISKOM.POL/2018/K_113_18.PDF) |
| Prawa jazdy | W 2023 r. wydano o ponad 150 tys. mniej praw jazdy niż w 2016 | 2023 | [auto-swiat.pl](https://www.auto-swiat.pl/wiadomosci/aktualnosci/mlodzi-nie-chca-prowadzic-samochodow-dramatyczny-spadek-liczby-praw-jazdy/jnhdbcf) |
| Przejazdy studentów i doktorantów w PKP IC | **13,7 mln** (+17%) | 2025 | [PKP IC](https://www.intercity.pl/pl/site/o-nas/dzial-prasowy/aktualnosci/pkp-intercity:-podroze-koleja-w-2025-roku.html) |

### 3.2 Założenia (SZACUNKI, do zmiany w arkuszu `Zalozenia`)

| Założenie | Wartość | Uzasadnienie |
|---|---|---|
| % mieszkających poza domem rodzinnym | 50% | Eurostudent: ok. połowa mieszka z rodzicami |
| % z nich jeżdżących regularnie (≥ 1×/mies.) między miastami | 60% | **Brak danych**, to pytanie nr 1 do ankiety |
| Przejazdy w jedną stronę / osobę / rok | 24 | ok. 12 powrotów w obie strony |
| Średnia cena miejsca | 30 zł | konkurencja z IC z ulgą (~25–27 zł) |
| % otwartych na carpooling | 35% | brak danych |
| Udział ich przejazdów robionych autem | 40% | część podróży i tak pociągiem |
| % kierowców | 20% | proxy z CBOS (2018) |
| Prowizja | 12% | BlaBlaCar PL ~13% |

### 3.3 Obliczenia (wzory)

| Pozycja | Wzór | Wynik |
|---|---|---|
| Studenci krajowi | 1 322 841 − 108 600 | 1 214 241 |
| Poza domem | × 50% | 607 120 |
| **TAM (osoby)** | × 60% | **≈ 364 tys. studentów** |
| TAM (przejazdy/rok) | × 24 | ≈ 8,7 mln |
| TAM (GMV, teoretycznie) | × 30 zł | ≈ 262 mln zł |
| *Kontrola* | PKP IC: 13,7 mln przejazdów studentów i doktorantów w 2025 r. | rząd wielkości zgodny |
| **SAM (osoby)** | TAM × 35% | **≈ 127 tys.** |
| SAM (przejazdy autem/rok) | × 24 × 40% | ≈ 1,22 mln |
| SAM (GMV) | × 30 zł | ≈ 36,7 mln zł |
| **Sufit przychodu z prowizji (100% SAM)** | × 3,60 zł | **≈ 4,4 mln zł brutto / ≈ 2,6 mln zł netto po płatnościach** |
| Kontrola podaży | kierowcy (20% SAM) × 24 × 40% × 3 miejsca vs popyt pasażerów | podaż pokrywa ok. **0,75×** popytu, więc **brakuje kierowców** |
| **SOM: korytarz Warszawa↔Lublin** | (257 tys. × 6% z lubelskiego + 58,2 tys. × 8% z Mazowsza) × 60% × 35% | ≈ **4,2 tys.** osób osiągalnych |
| SOM rok 1 (korytarz) | × 10% | **≈ 420 aktywnych użytkowników** |
| Przejazdy w korytarzu na weekend (przy 100% rynku osiągalnego) | 4,2 tys. × 24 × 40% / 35 weekendów | ≈ 1 150 |

**SOM dla aplikacji w latach 1–3 (aktywni użytkownicy = co najmniej 1 przejazd w roku):**

| Scenariusz | Rok 1 | Rok 2 | Rok 3 | Założenie |
|---|---|---|---|---|
| Pesymistyczny | 300 | 1 000 | 2 500 | 1 korytarz, słaby wzrost |
| Bazowy | 800 | 4 000 | 12 000 | 1–2 korytarze, potem ok. 5 tras wschód–Warszawa i południe |
| Optymistyczny | 2 000 | 10 000 | 30 000 | ok. 15 korytarzy, partnerstwa z uczelniami |

**Wniosek:** nawet optymistyczne 30 tys. użytkowników to ~24% krajowego SAM i ~0,5% liczby aktywnych użytkowników BlaBlaCar w Polsce. **Rynek wystarcza na projekt społeczny lub mały biznes, ale nie na startup venture.**

---

## 4. Walidacja pomysłu

### 4.1 Ograniczenie tylko do studentów: plusy i minusy

| Mocne strony | Słabe strony |
|---|---|
| Zaufanie: weryfikacja e-mailem uczelnianym, „swoi” | **Mniejsza sieć niż BlaBlaCar**, więc mniej ofert na konkretną godzinę |
| Gęste skupiska (kampusy, akademiki), tani marketing szeptany | **Niska siła nabywcza** i ulga 51% na kolei, więc niska cena i mała prowizja |
| Przewidywalne szczyty (piątek/niedziela, święta) | **Sezonowość**: lipiec–wrzesień prawie zero, sesje słabsze |
| Kanały: samorządy, koła, akademiki, grupy regionalne | **Mało kierowców**: ok. 20% ma auto, liczba nowych praw jazdy spada |
| Społeczność i wspólne zainteresowania (wartość dodana) | **Naturalny churn**: absolwenci odchodzą co roku |
| | **Młodzi kierowcy**: grupa 18–24 ma najwyższy wskaźnik wypadków na 10 tys. osób (KGP, „Wypadki drogowe w Polsce w 2023 r.”, za doniesieniami prasowymi) |

### 4.2 Kwestie prawne

> To nie jest porada prawna. Przed uruchomieniem płatności zamów opinię prawnika (koszt szacuję na kilka–kilkanaście tys. zł).

| Obszar | Stan prawny / fakty | Ryzyko i co zrobić |
|---|---|---|
| **Przewóz osób** | „Lex Uber” (nowelizacja ustawy o transporcie drogowym, w mocy od 1.01.2020, kluczowe obowiązki od 1.10.2020): płatny przewóz osób autem osobowym wymaga licencji taxi, a **pośrednictwo przy przewozie osób** (aplikacje) wymaga licencji pośrednika ([prawodrogowe.pl](https://www.prawodrogowe.pl/informacje/kronika-legislacyjna/od-dzis-posrednik-organizujacy-przewoz-osob-tylko-z-licencja), [gazetaprawna.pl](https://www.gazetaprawna.pl/biznes/transport/artykuly/11098201,lex-uber-licencja-taxi-posrednicy-elektroniczny-rejestr-zlecenia-przewozowe.html)). Carpooling oparty na dzieleniu kosztów, gdy kierowca jedzie we własnym celu, nie jest działalnością gospodarczą. | **Nie znalazłem wprost przepisu wyłączającego carpooling.** BlaBlaCar działa w PL od 2012 r. na zasadzie dzielenia kosztów. Ryzyko pojawia się, gdy kierowcy zaczną zarabiać, bo wtedy to nielegalna taksówka, a platforma może zostać uznana za pośrednika bez licencji. Zabezpieczenia: limit ceny za km (jak Poparide), kalkulator kosztów, brak przejazdów „na zamówienie” pasażera. |
| **Podatki: kierowca** | Ministerstwo Finansów (odpowiedź na interpelację nr 32705): zwrot części kosztów przejazdu nie jest przychodem w PIT; nadwyżka ponad koszty podlega opodatkowaniu ([bankier.pl](https://www.bankier.pl/wiadomosc/Kierowca-BlaBlaCar-nie-placi-podatkow-i-nie-jest-przedsiebiorca-3723204.html), [infor.pl](https://ksiegowosc.infor.pl/podatki/pit/724418,Wspolne-przejazdy-skutki-podatkowe.html)) | Komunikuj kierowcom zasadę „tylko koszty” |
| **Podatki: platforma** | Opłata serwisowa to Twój przychód z VAT 23% (BlaBlaCar w 2016 doliczał 23% VAT). **DAC7**: unijne raportowanie operatorów platform od 1.01.2023. We Francji BlaBlaCar raportuje dane kierowców ([l-itineraire.com](https://www.l-itineraire.com/mobilite/covoiturage/frais-covoiturage-bareme-fiscalite), [Deloitte](https://blog.avocats.deloitte.fr/dac7-les-obligations-declaratives-des-operateurs-de-plateformes-precisees-par-decret-et-arrete-et-commentees-au-bofip/)) | Sprawdź z doradcą, czy i jak polskie wdrożenie DAC7 obejmie wypłaty dla kierowców |
| **Płatności** | Przyjmowanie pieniędzy pasażera i przekazywanie ich kierowcy to usługa płatnicza (PSD2) | Nie trzymaj cudzych pieniędzy sam (wymagałoby to zezwolenia KNF). Użyj licencjonowanego operatora (np. marketplace w Stripe; BlaBlaCar PL używa Hyperwallet). |
| **Odpowiedzialność za wypadek** | Kodeks cywilny, art. 436 § 2: przy przewozie **z grzeczności** kierowca odpowiada na zasadach ogólnych (wina). Przy przejeździe odpłatnym, także przy dzieleniu kosztów, według mubi.pl odpowiada na zasadzie ryzyka. Szkody pasażera pokrywa OC posiadacza pojazdu, a NNW jest dobrowolne ([mubi.pl](https://mubi.pl/poradniki/carpooling-a-ubezpieczenie/), [standardyprawa.pl](https://standardyprawa.pl/akt/2/art/4520)) | W regulaminie: platforma jest pośrednikiem informacyjnym. Rozważ grupowe NNW (do wyceny u brokera). Wymagaj ważnego OC i prawa jazdy od co najmniej 1–2 lat. |
| **RODO** | Numery telefonów, lokalizacje, dane z legitymacji | Weryfikuj **przez e-mail uczelniany**, nie skan legitymacji (nie przechowuj PESEL). Polityka prywatności, umowy powierzenia (hosting, SMS), minimalny czas przechowywania. Rozważ ocenę skutków (DPIA) dla danych lokalizacyjnych. |
| **Platformy cyfrowe** | Akt o usługach cyfrowych (DSA) i ustawa o świadczeniu usług drogą elektroniczną: regulamin, procedura zgłaszania nadużyć, punkt kontaktowy. Mikro- i małe firmy są zwolnione z części obowiązków DSA. | Regulamin i mechanizm zgłoszeń od pierwszego dnia |

### 4.3 Bezpieczeństwo

- Główne ryzyka: wypadek z udziałem niedoświadczonego kierowcy, nękanie lub napaść (szczególnie wobec pasażerek), oszustwa płatnicze (fałszywe linki, jak w przypadku podróbek BlaBlaCar), nieodbycie przejazdu.
- Środki zaradcze: weryfikacja e-mailem uczelnianym i numerem telefonu, profile ze zdjęciem, obustronne oceny, udostępnianie trasy znajomym, opcja „tylko kobiety” (do sprawdzenia prawnie), zakaz płatności poza aplikacją przez linki, szybkie blokowanie kont.
- Jedno głośne zdarzenie może zabić markę opartą na zaufaniu, a w małej społeczności studenckiej plotka rozchodzi się szybko w obie strony.

### 4.4 Sezonowość (SZACUNEK indeksu popytu, średni miesiąc ≈ 1,0)

| Miesiąc | Indeks | Dlaczego |
|---|---|---|
| Październik | 1,0 | Start roku. W 2026 r. weekend 30.10–1.11 (Wszystkich Świętych w niedzielę) to szczyt. |
| Listopad | 1,1 | 11.11 (środa), weekendy |
| Grudzień | 1,3 | Boże Narodzenie (szczyt ok. 18–23.12) |
| Styczeń | 0,8 | Sesja |
| Luty | 0,7 | Sesja i przerwa międzysemestralna |
| Marzec–kwiecień | 0,9–1,1 | Wielkanoc |
| Maj | 1,0 | Majówka, juwenalia |
| Czerwiec | 0,8 | Sesja, wyprowadzki z bagażem |
| Lipiec–sierpień | 0,1–0,2 | Wakacje, studenci w domach |
| Wrzesień | 0,3 | Przeprowadzki pod koniec miesiąca |

**Skutek:** ok. 9 „efektywnych” miesięcy przychodu przy 12 miesiącach kosztów stałych. Ok. 30–35 weekendów robi większość wolumenu.

### 4.5 Jak rozwiązać „kurę i jajko” na starcie

1. **Jedna trasa, dwa okna czasowe:** Warszawa → Lublin w piątek 14–19, Lublin → Warszawa w niedzielę 15–20. 2–3 stałe punkty odbioru przy metrze lub kampusach.
2. **Najpierw kierowcy (strona deficytowa).** Zwerbuj 20–30 kierowców, którzy i tak jeżdżą tą trasą. Dla nich: zero opłat, gwarancja pasażerów, odznaka „kierowca-założyciel”, ewentualnie bon paliwowy od sponsora.
3. **Concierge MVP:** ręczne dopasowywanie przez WhatsApp lub Telegram i formularz. Aplikację buduj dopiero po potwierdzeniu popytu.
4. **Pasożytuj na istniejących kanałach, nie walcz z nimi.** Publikuj przejazdy w istniejących grupach FB, w grupach regionalnych, akademikach i samorządach.
5. **Stałe ekipy:** zachęcaj do cyklicznych przejazdów co tydzień, bo to buduje retencję.
6. **Ambasadorzy:** jedna osoba na kampus, wynagradzana za aktywowanego kierowcę (np. ≥ 2 przejazdy).
7. **Start w szczycie:** Wszystkich Świętych (30.10–1.11.2026) i powroty na święta (18–23.12.2026).
8. **Uczelnie:** biura zrównoważonego rozwoju i samorządy (precedens PWr i otodojazd.pl). Na kanał dystrybucji i zaufanie, a nie na szybki przychód.

### 4.6 Ryzyka i ocena szans

| Ryzyko | Prawdop. | Wpływ | Komentarz |
|---|---|---|---|
| Studenci wybiorą pociąg z ulgą 51% | Wysokie | Wysoki | Kolej rośnie (+17% przejazdów studentów w PKP IC w 2025) |
| Za mało kierowców | Wysokie | Wysoki | Wskaźnik podaży ~0,75× w modelu |
| BlaBlaCar i grupy FB już „wystarczają” | Wysokie | Wysoki | Efekt sieciowy lidera |
| Niska monetyzacja (2 zł netto na rezerwację) | Pewne | Wysoki | Opłata stała operatora płatności zjada marżę |
| Disintermediation (umawianie się poza aplikacją) | Wysokie | Średni | Stałe ekipy nie potrzebują aplikacji po pierwszym kontakcie |
| Sezonowość i churn absolwentów | Pewne | Średni | |
| Incydent bezpieczeństwa | Niskie | Bardzo wysoki | |
| Kwalifikacja prawna (pośrednictwo, DAC7) | Średnie | Średni | Wymaga opinii prawnika |

**Ocena szans: 3/10 jako samodzielny, rentowny biznes.**
- Za: realny problem, łatwy dostęp do grupy docelowej, bardzo tani test, zaufanie jako wyróżnik.
- Przeciw: tani i szybki substytut (kolej z ulgą), silny lider (BlaBlaCar) plus darmowe grupy FB, niska wartość transakcji, mało kierowców, sezonowość. Do tego historia analogów: Zimride porzucony przez założycieli, YanosikTLS, Waze Carpool.

Jako projekt po godzinach, który pokrywa własne koszty i daje doświadczenie, oceniam szanse na ok. 5/10.

---

## 5. Monetyzacja

### 5.1 Siedem modeli: przychód netto rocznie (po kosztach operatora płatności, przed kosztami firmy)

Założenia: 75% aktywnych to pasażerowie, 8 rezerwacji przez aplikację na pasażera rocznie, cena miejsca 30 zł, Stripe 1,5% + 1 zł (karty) i 1,6% + 1 zł (BLIK) ([quasa.io](https://quasa.io/pl/media/stripe-czy-payu-stala-zlotowka-boli-najbardziej-przy-malym-koszyku)).

| Model | Opłata (SZAC.) | Na użytk./rok | **1 000** | **10 000** | **50 000** | Zalety | Wady |
|---|---|---|---|---|---|---|---|
| 1. Prowizja od przejazdu | 12% (3,60 zł; netto 2,10 zł) | 12,58 zł | 12,6 tys. zł | 126 tys. zł | 629 tys. zł | Standard rynku, skaluje się, mniej odwołań | Mała kwota, bo stała opłata 1 zł zjada marżę; ucieczka do darmowych grup |
| 2. Stała opłata za rezerwację | 2,99 zł (paliwo BLIK-iem do kierowcy) | 11,65 zł | 11,7 tys. zł | 117 tys. zł | 583 tys. zł | Prosta; nie trzymasz pieniędzy kierowców | Umawianie się poza aplikacją |
| 3. Subskrypcja „Semestr Pass” | 29 zł/semestr, 10% pasażerów | 4,13 zł | 4,1 tys. zł | 41 tys. zł | 207 tys. zł | Przewidywalna, jedna transakcja | Niska konwersja, puste lato |
| 4. Premium dla kierowców | 9,99 zł/mies., 5% kierowców | 0,99 zł | 1,0 tys. zł | 9,9 tys. zł | 50 tys. zł | Nie obciąża pasażerów | Zniechęca stronę deficytową |
| 5. Reklamy i partnerstwa (banki, telekomy, gastronomia) | ~5 zł/użytk./rok od 5 tys. użytk. | — | 0 | 50 tys. zł | 250 tys. zł | Nie obciąża użytkowników | Wymaga skali, nieregularne |
| 6. Licencje dla uczelni (B2B2C) | 15 tys. zł/uczelnię; 1 uczelnia na 5 tys. użytk. | — | 0 | 30 tys. zł | 150 tys. zł | Zaufanie i dystrybucja (PWr, Zimride) | Zamówienia publiczne, wolne decyzje |
| 7. Afiliacja i oferty firm (bilety, gdy brak przejazdu; NNW; paliwo) | ~2 zł/użytk./rok | 2,00 zł | 2 tys. zł | 20 tys. zł | 100 tys. zł | Monetyzuje nieudane wyszukiwania | Niskie stawki; dystrybucja ubezpieczeń wymaga zgodności z IDD |
| **Miks docelowy 1+5+6+7** | | | **14,6 tys. zł** | **226 tys. zł** | **1,13 mln zł** | | |

Modele 1–3 to warianty tej samej opłaty od pasażera, więc ich nie sumuj. Szczegóły i formuły są w arkuszu `Monetyzacja`.

### 5.2 Rekomendacja

- **Start (pierwsze 6–12 miesięcy):** za darmo dla wszystkich. Przychód nie ma znaczenia, liczy się płynność. Po ok. 2 miesiącach przetestuj gotowość do płacenia: opłata za rezerwację 2–3 zł dla części użytkowników.
- **Później:** opłata pasażera (stała albo %), ale **z doładowaniem portfela** (np. 20 zł naraz), żeby rozłożyć stałą opłatę operatora płatności. Dalej partnerstwa z markami studenckimi od ok. 5 tys. użytkowników, licencje lub projekty z uczelniami i pracodawcami, afiliacja biletów kolejowych i autobusowych.
- **Nie rób:** subskrypcji dla kierowców ani reklam od pierwszego dnia.

### 5.3 Uproszczony model finansowy (3 lata, zł; arkusz `Scenariusze`)

**Główne założenia kosztowe (SZACUNKI):**

| Koszt | Wartość | Źródło / uzasadnienie |
|---|---|---|
| MVP natywne w software house | 25–60 tys. USD (ok. 90–220 tys. zł) | [netguru.com](https://www.netguru.com/pl/blog/koszt-tworzenia-aplikacji-mobilnej), [techsy.io](https://techsy.io/pl/blog/how-much-does-it-cost-to-build-a-mobile-app-in-2026) |
| Serwery | 150–600 zł/mies.; konta deweloperskie: Google ok. 100 zł jednorazowo, Apple ok. 400 zł/rok | [cenauslug.pl](https://cenauslug.pl/poradniki/koszt-stworzenia-aplikacji-mobilnej-analiza-ux-design-i-dev) |
| CAC (pozyskanie aktywnego użytkownika) | Instalacja w Europie: Android 1,41 USD, iOS 2,31 USD ([mapendo.co](https://mapendo.co/blog/cost-per-install-by-country-2025)); przy 25% konwersji instalacja → aktywny wychodzi **ok. 28 zł** z płatnych kampanii, a przy 50% użytkowników organicznych ok. 14 zł | |
| Prawnik | 8–15 tys. zł w roku 1 | szacunek |
| Księgowość | 6 tys. zł/rok | szacunek |
| Ubezpieczenie | 3 tys. zł/rok | szacunek |
| Obsługa klienta | 3 zł na użytkownika rocznie | szacunek |
| Wynagrodzenia | 0 w wariancie pesymistycznym; w bazowym 0 / 120 / 240 tys. zł; w optymistycznym 60 / 360 / 600 tys. zł | szacunek |
| Rok 1 | Bez opłat od pasażerów we wszystkich scenariuszach | założenie |

**Wyniki:**

| | Pes. R1 | Pes. R2 | Pes. R3 | Baz. R1 | Baz. R2 | Baz. R3 | Opt. R1 | Opt. R2 | Opt. R3 |
|---|---|---|---|---|---|---|---|---|---|
| Aktywni użytkownicy | 300 | 1 000 | 2 500 | 800 | 4 000 | 12 000 | 2 000 | 10 000 | 30 000 |
| GMV | 54 tys. | 180 tys. | 450 tys. | 144 tys. | 720 tys. | 2,16 mln | 360 tys. | 1,8 mln | 5,4 mln |
| **Przychody** | 0,6 tys. | 14,6 tys. | 36 tys. | 1,6 tys. | 58 tys. | 265 tys. | 4 tys. | 226 tys. | 677 tys. |
| **Koszty** | 38 tys. | 56 tys. | 89 tys. | 74 tys. | 275 tys. | 565 tys. | 282 tys. | 716 tys. | 1,32 mln |
| **Wynik roczny** | −38 tys. | −41 tys. | −53 tys. | −72 tys. | −217 tys. | −300 tys. | −278 tys. | −491 tys. | −640 tys. |
| **Wynik skumulowany** | −38 tys. | −79 tys. | **−131 tys.** | −72 tys. | −289 tys. | **−589 tys.** | −278 tys. | −769 tys. | **−1,41 mln** |
| Próg rentowności (aktywni) | ~2,5 tys. | ~3,1 tys. | ~4,1 tys. | ~4,5 tys. | ~16 tys. | ~29 tys. | ~19 tys. | ~42 tys. | ~66 tys. |
| Próg jako % krajowego SAM | 2% | 2% | 3% | 4% | 13% | 23% | 15% | 33% | 52% |

**Próg rentowności (break-even):** przy pełnej monetyzacji jeden aktywny użytkownik daje ok. 22,6 zł przychodu rocznie, a kosztuje ok. 9,2 zł (infrastruktura, obsługa, odtworzenie churnu). **Na każdego użytkownika zostaje ~13 zł marży.**
- Bez wynagrodzeń (koszty stałe ~33–60 tys. zł/rok) wystarczy **~2,5–4,5 tys. aktywnych użytkowników**. To realne, ale oznacza darmową pracę założycieli.
- Z zespołem 2 osób (koszty stałe ~210–390 tys. zł/rok) potrzeba **~16–29 tys. aktywnych użytkowników**, czyli 13–23% całego krajowego SAM w walce z BlaBlaCar. To mało realne w 3 lata.
- Żaden scenariusz nie wychodzi na plus w ciągu 3 lat.

---

## 6. Plan wejścia na rynek (MVP)

### 6.1 Warianty MVP

| Wariant | Koszt (SZAC.) | Czas | Kiedy |
|---|---|---|---|
| A. Grupa WhatsApp/Telegram + formularz (Google Forms/Tally) + arkusz | 0–100 zł | 1–3 dni | **Start: test popytu** |
| B. A + landing page (np. Carrd, Framer, Notion) z listą zapisów | 50–300 zł/rok (domena + narzędzie; sprawdź aktualne cenniki) | 1 tydzień | Równolegle z A |
| C. Aplikacja no-code (np. Glide, Softr, Bubble, FlutterFlow) | darmowe plany albo kilkadziesiąt–kilkaset zł/mies. + Twój czas | 3–6 tygodni | Po potwierdzeniu popytu (≥ 30 przejazdów/tydzień) |
| D. Aplikacja natywna (software house) | ok. 90–220 tys. zł (25–60 tys. USD) | 2–4 miesiące | Dopiero przy dowodzie trakcji i finansowaniu |

### 6.2 Plan 8 tygodni (7.10–1.12.2026)

| Tydzień | Działania | Cel |
|---|---|---|
| 1 (7–13.10) | 20–30 rozmów ze studentami z Lubelszczyzny w Warszawie. Ankieta (cel: 200+ odpowiedzi) w grupach FB, akademikach i samorządach. | Częstotliwość powrotów, obecny środek transportu, cena, gotowość do zabierania pasażerów |
| 2 (14–20.10) | Landing page i lista zapisów. Grupa „Warszawa ↔ Lublin – studenci” z weryfikacją e-mailem uczelnianym (ręcznie). Werbowanie kierowców. | ≥ 300 zapisów, ≥ 20% kierowców |
| 3–4 (21.10–3.11) | Concierge matching na piątki i niedziele. **Test szczytowy: Wszystkich Świętych 30.10–1.11.** | ≥ 30 zrealizowanych przejazdów w weekend 30.10–1.11 |
| 5–6 (4–17.11) | Pomiar retencji. Test gotowości do płacenia (2–3 zł przez BLIK/link za „gwarancję miejsca”) dla połowy użytkowników. | Powtórne przejazdy, konwersja płatności |
| 7–8 (18.11–1.12) | Zapisy na powroty świąteczne (18–23.12). Rozmowa z 1–2 uczelniami lub samorządami. Decyzja: dalej, pivot czy stop. | Decyzja na podstawie KPI |

### 6.3 KPI i progi decyzji (moje heurystyki, nie normy rynkowe)

| KPI | Cel (kontynuuj) | Próg pivotu / stopu |
|---|---|---|
| Zapisy na liście (2 tygodnie promocji) | ≥ 300 | < 100 |
| Udział kierowców wśród zapisów | ≥ 20% | < 10% |
| Skuteczność dopasowania (zapytania → przejazd) | ≥ 60% | < 40% |
| Zrealizowane przejazdy / weekend (od tygodnia 4) | ≥ 30 | < 10 |
| Powtórny przejazd pasażera w ciągu 3 tygodni | ≥ 40% | < 20% |
| Gotowość do zapłaty 2–3 zł | ≥ 30% | < 10% |
| Nowi użytkownicy z poleceń | ≥ 30% | < 10% |

**Kiedy pivotować:** popyt jest, ale kierowców brak, więc warto sprawdzić model ze **zorganizowanym busem** (patrz 7.3). Ludzie jeżdżą, ale nikt nie zapłaci, więc zostaw to jako darmową społeczność albo projekt z uczelnią.
**Kiedy zrezygnować:** mniej niż 100 zapisów i mniej niż 10 kierowców po 3 tygodniach aktywnej promocji.

### 6.4 Najważniejsze pytania do ankiety

1. Jak często jeździsz do domu (co tydzień / co 2 tygodnie / raz w miesiącu / tylko na święta)? Dokąd?
2. Czym jeździsz dziś i ile płacisz?
3. Masz auto w mieście studiów? Ile wolnych miejsc i jak często jedziesz?
4. Czy pojechałbyś lub pojechałabyś z innym zweryfikowanym studentem? Co by Cię powstrzymało?
5. Ile maksymalnie zapłaciłbyś lub zapłaciłabyś za miejsce? Czy zapłaciłbyś lub zapłaciłabyś 2–3 zł za gwarancję miejsca?
6. Czy korzystasz z BlaBlaCar lub grup na FB? Co Ci w nich przeszkadza?

---

## 7. Werdykt

### **Warto z zastrzeżeniami**

**Warto** zrobić tani test (≤ 500 zł, 6–8 tygodni) na trasie Warszawa ↔ Lublin w formie concierge. To Twój własny problem, masz dostęp do grupy docelowej, a w najbliższych tygodniach są dwa naturalne szczyty popytu (Wszystkich Świętych i święta).
**Nie warto** budować i finansować pełnej aplikacji jako samodzielnego, rentownego startupu. Sufit przychodu w całym studenckim SAM to ok. 2,6–4,4 mln zł rocznie przy 100% udziału. Prowizja netto to ok. 2 zł na przejazd, a model bazowy daje −0,59 mln zł po 3 latach.

### 3 najważniejsze ryzyka
1. **Pociąg z ulgą 51%** (~25–27 zł, poniżej 2 h na trasach ~170 km) ustala bardzo niski sufit ceny.
2. **Za mało kierowców i efekt sieciowy BlaBlaCar plus darmowe grupy FB.** Studencka sieć ma mniej ofert, nie więcej.
3. **Monetyzacja i sezonowość:** ~2 zł netto na rezerwację, puste lato, coroczny odpływ absolwentów.

### 3 najważniejsze szanse
1. **Zaufanie** (weryfikacja przez uczelnię), szczególnie dla pasażerek.
2. **Stałe ekipy i szczyty** (piątki i niedziele, święta, przeprowadzki z bagażem), których BlaBlaCar nie obsługuje specjalnie.
3. **Kanał instytucjonalny:** uczelnie i samorządy (precedens PWr i otodojazd), sponsorzy celujący w studentów.

### 7.3 Alternatywne warianty o większych szansach

| Wariant | Opis | Dlaczego lepiej | Szanse (1–10) |
|---|---|---|---|
| **A. „Stałe ekipy” dla młodych dorosłych 18–30 na 2–3 korytarzach wschód ↔ Warszawa** | Studenci plus młodzi pracujący, którzy jeżdżą co tydzień | Więcej kierowców (pracujący mają auta), wyższa siła nabywcza, ten sam ból | 4 |
| **B. Studencki bus na zamówienie (crowdfunding miejsc)** | Zbierasz zapisy, a licencjonowany przewoźnik wozi 9–20 osób w piątek i niedzielę | Jasny status prawny (przewoźnik z licencją), lepsza marża na miejscu, nie potrzeba kierowców-studentów | 4–5 |
| **C. Carpooling na wydarzenia** (juwenalia, festiwale, koncerty, wyjazdy kół) | Partnerstwa z organizatorami | Wysoka gotowość do płacenia, sponsorzy, marketing przez organizatora | 4 |
| **D. B2B2C dla uczelni i pracodawców (dojazdy na kampus)** | White-label, uczelnia płaci | Zaufanie i dystrybucja; cele klimatyczne uczelni | 3 (wolna sprzedaż, małe budżety, przykład Zimride) |
| **E. Funkcja w istniejącym ekosystemie** (samorząd, aplikacja uczelni, partnerstwo z BlaBlaCar jako ambasador) | Bez własnej platformy | Minimalny koszt, wykorzystanie cudzej płynności | 6 jako projekt, 1 jako biznes |

**Moja rekomendacja:** zacznij od testu concierge na trasie Warszawa ↔ Lublin. Jeśli podaż kierowców będzie za słaba, przetestuj wariant B (bus), a jeśli zainteresowanie wykażą pracujący 20–30-latkowie, wariant A.

---

## Źródła

Pełna lista z linkami jest w arkuszu `Zrodla` w pliku [`model-carpooling-studenci.xlsx`](model-carpooling-studenci.xlsx). Najważniejsze:
- GUS: [Szkolnictwo wyższe w roku akademickim 2025/2026](https://stat.gov.pl/obszary-tematyczne/edukacja/edukacja/szkolnictwo-wyzsze-w-roku-akademickim-20252026,8,12.html); [prawo.pl](https://www.prawo.pl/szkoly-i-uczelnie/liczba-studentow-w-polsce-w-roku-akademickim-2025-26-gus,1546639.html); [isr.info.pl](https://www.isr.info.pl/studenci-lgna-do-czterech-wojewodztw/)
- [PKP Intercity – podsumowanie 2025](https://www.intercity.pl/pl/site/o-nas/dzial-prasowy/aktualnosci/pkp-intercity:-podroze-koleja-w-2025-roku.html); [ulgi ustawowe](https://www.intercity.pl/pl/site/dla-pasazera/kup-bilet/przepisy-i-taryfy/ulgi/ulgi-ustawowe/)
- BlaBlaCar: [newsroom 2024](https://newsroom.blablacar.com/news/blablacar-closes-financing-round-to-fuel-its-growth-ambitions); [TechCrunch](https://techcrunch.com/2024/04/02/after-reaching-profitability-carpooling-platform-blablacar-secures-108-million-debt-line); [newmobility.news 2026](https://newmobility.news/en/2026/04/22/blablacar-is-shutting-down-its-bus-division-in-france/); [antyweb.pl – wyniki 2023](https://antyweb.pl/blablacar-wyniki-2023); [bankier.pl – opłaty 2016](https://www.bankier.pl/wiadomosc/BlaBlaCar-wprowadza-oplaty-za-przejazdy-Rozwoj-kosztuje-7336289.html)
- [Eurostudent VIII (PBS)](https://pbs.pl/jak-sie-zyje-i-studiuje-w-polsce-eurostudent-viii/); [CBRE](https://biuroprasowe.cbre.pl/97638-w-akademikach-mieszka-co-dziesiaty-student-powod-jest-prosty-tyle-jest-miejsc); [Knight Frank](https://content.knightfrank.com/research/2849/documents/pl/prywatne-akademiki-w-polsce-2025-12323.pdf)
- [Zimride](https://en.wikipedia.org/wiki/Zimride); [Waze Carpool](https://9to5google.com/2022/08/25/waze-carpool-shut-down/); [UberX Share](https://edition.cnn.com/2022/06/21/tech/uber-restarting-shared-rides); [Hitch](https://fortune.com/2014/10/15/hitch-lyft-acquisition); [Scoop](https://layoffs.fyi/2020/12/02/scoop-conducts-second-layoff-of-2020/); [PolskiBus](https://en.wikipedia.org/wiki/PolskiBus)
- Prawo: [prawodrogowe.pl](https://www.prawodrogowe.pl/informacje/kronika-legislacyjna/od-dzis-posrednik-organizujacy-przewoz-osob-tylko-z-licencja); [bankier.pl – podatki](https://www.bankier.pl/wiadomosc/Kierowca-BlaBlaCar-nie-placi-podatkow-i-nie-jest-przedsiebiorca-3723204.html); [mubi.pl](https://mubi.pl/poradniki/carpooling-a-ubezpieczenie/)
