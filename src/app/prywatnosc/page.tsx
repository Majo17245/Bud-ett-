export const metadata = { title: 'Prywatność' };

export default function Privacy() {
  return (
    <main className="narrow">
      <div className="flash info">Projekt polityki prywatności do weryfikacji przez prawnika.</div>
      <h1>Prywatność i dane osobowe</h1>
      <ul className="soft stack">
        <li><strong>Administrator danych gości</strong> to klub lub organizator wydarzenia. Klubowy przetwarza dane w jego imieniu na podstawie umowy powierzenia (art. 28 RODO).</li>
        <li><strong>Zakres:</strong> imię i nazwisko, e-mail, opcjonalnie telefon, historia zakupów i wejść. Nie przechowujemy zdjęć ani kopii dokumentów tożsamości; wiek jest sprawdzany na wejściu, a system zapisuje najwyżej wynik „tak/nie”.</li>
        <li><strong>Cel:</strong> realizacja zamówienia i wejścia na wydarzenie (art. 6 ust. 1 lit. b RODO); marketing klubu wyłącznie po wyrażeniu osobnej zgody (art. 6 ust. 1 lit. a), którą można wycofać w każdej chwili.</li>
        <li><strong>Przechowywanie:</strong> dane zamówień przez okres wymagany przepisami podatkowymi; dane marketingowe do wycofania zgody; dzienniki bramki do 12 miesięcy.</li>
        <li><strong>Lokalizacja:</strong> dane przechowujemy na serwerach w Unii Europejskiej (Frankfurt).</li>
        <li><strong>Prawa:</strong> dostęp, sprostowanie, usunięcie, ograniczenie, przeniesienie, sprzeciw, skarga do Prezesa UODO.</li>
      </ul>
    </main>
  );
}
