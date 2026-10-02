export const metadata = { title: 'Regulamin' };

export default function Terms() {
  return (
    <main className="narrow">
      <div className="flash info">Projekt regulaminu przygotowany do weryfikacji przez prawnika — nie publikować bez sprawdzenia.</div>
      <h1>Regulamin sprzedaży biletów i rezerwacji</h1>
      <ol className="soft stack">
        <li>Sprzedawcą biletów i usług (wstęp, rezerwacja loży) jest klub lub organizator wskazany na stronie wydarzenia. Klubowy udostępnia system sprzedaży i obsługi wejść.</li>
        <li>Płatności obsługuje licencjonowany operator płatności (np. Przelewy24). Środki trafiają na rachunek sprzedawcy u operatora; Klubowy nie przechowuje danych kart płatniczych.</li>
        <li>Opłata serwisowa, jeśli występuje, jest pokazywana przed zakupem i obejmuje koszty płatności.</li>
        <li>Zgodnie z art. 38 ust. 1 pkt 12 ustawy o prawach konsumenta prawo odstąpienia od umowy zawartej na odległość nie przysługuje w przypadku usług związanych z wydarzeniami rozrywkowymi, jeżeli umowa oznacza dzień lub okres świadczenia usługi.</li>
        <li>Zwrot ceny biletu przysługuje w razie odwołania wydarzenia. W razie zmiany terminu kupujący może zachować bilet lub zażądać zwrotu w terminie wskazanym przez sprzedawcę.</li>
        <li>Przedpłata za lożę jest zaliczana na poczet minimalnego wydatku w dniu wydarzenia. Niestawienie się nie uprawnia do zwrotu przedpłaty, chyba że sprzedawca postanowi inaczej.</li>
        <li>Bilet to jednorazowy kod QR. Kod wykorzystany przy wejściu traci ważność. Nie udostępniaj zrzutu ekranu kodu — wejdzie osoba, która pokaże go pierwsza.</li>
        <li>Wstęp na wydarzenia z ograniczeniem wieku wymaga potwierdzenia wieku na wejściu (dokument lub mObywatel). Klub może odmówić wstępu osobom, które nie spełniają warunków lub naruszają regulamin lokalu.</li>
        <li>Reklamacje dotyczące działania systemu można składać na adres kontaktowy klubu lub Klubowego; odpowiedź w ciągu 14 dni.</li>
      </ol>
    </main>
  );
}
