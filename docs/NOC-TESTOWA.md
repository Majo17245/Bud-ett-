# Noc testowa — scenariusz

Plan ekspresowy z biznesplanu: noc testowa 16–17 października (listy, bramka, loże bez płatności online),
Halloween 30–31 października — pierwsza sprzedaż online.

## Konfiguracja klubu (15 minut)

1. Załóż konto (`/rejestracja`) — plan Start, płatności „brak”.
2. *Loże i sala*: dodaj loże z cenami i ustaw je na mapie (X/Y w procentach planu sali).
3. *Promotorzy*: dodaj promotorów, wyślij im prywatne linki do panelu.
4. *Imprezy → Nowa impreza*: ustaw limit osób i wiek. Dodaj bezpłatną pulę „Wejściówka z zaproszeniem”, jeśli
   klub chce zbierać zapisy online. Opublikuj.
5. *Listy gości*: listy dla promotorów i klubu, limit osób, „wejście z listy do” (np. 0:00).

## Test na sucho (dzień przed)

1. `npm run db:seed` na środowisku testowym daje 300 fikcyjnych zaproszeń w 4 listach.
2. Na 3 telefonach otwórz link do skanera z internetem (kod QR z zakładki *Bramka*). Sprawdź, że widać „300 kodów w telefonie”.
3. Włącz tryb samolotowy na wszystkich trzech. Skanuj zaproszenia (otwórz `/zaproszenie/KOD` na innym telefonie
   albo wydrukuj kilka). Sprawdź: zielony ekran, ponowny skan = czerwony „JUŻ UŻYTY”, lista po czasie = pomarańczowy.
4. Zeskanuj **ten sam kod** na dwóch telefonach offline. Po włączeniu sieci drugi telefon pokaże w historii,
   że serwer uznał skan za duplikat; raport pokaże „ponowny skan”.
5. Wydrukuj *Bramka → Lista do druku* (plan B przy awarii prądu/telefonów).
6. Zmierz czas wejścia jednej osoby (cel: 2–3 s zamiast 15–30 s).

## W noc imprezy

- 30 minut szkolenia ochrony: skan, wyszukiwanie po nazwisku, „+1 wejście (kasa)” dla płacących gotówką,
  „−1 wyjście” przy wyjściach (licznik w sali pilnuje limitu bezpieczeństwa).
- Ty przy bramce z laptopem: *Raport na żywo* odświeża się sam co 15 s.
- Notuj: czas wejścia, błędy, opinie bramkarzy, ile loż „na słowo” przepadło.
- Rano: raport poranny w skrzynce właściciela + rozmowa o płatnej współpracy od lutego.

## Mierniki do studium przypadku

udział sprzedaży online · odzyskane loże (przedpłata vs „na słowo”) · czas wejścia · liczba sporów z promotorami ·
odrzucone skany (próby wejścia na cudzy kod).
