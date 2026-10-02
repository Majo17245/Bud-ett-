import Link from 'next/link';
import { PLANS } from '@/lib/pricing';
import { zl } from '@/lib/money';

const FEATURES = [
  ['Loże z przedpłatą', 'Mapa sali, cena za osoby, przedpłata BLIK-iem. Koniec rezerwacji „na słowo”, po których loża stoi pusta.'],
  ['Promotorzy bez sporów', 'Własne linki i listy z limitem, ranking na żywo i prowizja, która liczy się sama.'],
  ['Jedna bramka', 'Skaner na każdym telefonie, działa bez internetu. Bilety, listy, loże i kody z RA czy Going w jednej kolejce.'],
  ['Pieniądze od razu u klubu', 'Płatność trafia na konto klubu u operatora — nie czekasz na wypłatę po imprezie.'],
  ['Listy gości z godziną', 'Limit osób, wejście do 23:30, blokada duplikatów między listami. Kartka na bramce przechodzi do historii.'],
  ['Raport na żywo', 'Ilu gości w sali, które kanały sprzedają, który promotor dowozi — w trakcie nocy, a rano podsumowanie.'],
];

export default function Landing() {
  return (
    <>
      <header className="topbar">
        <div className="topbar-inner">
          <span className="brand">klub<span>owy</span></span>
          <nav className="nav" />
          <Link href="/logowanie" className="btn ghost small">Zaloguj</Link>
          <Link href="/rejestracja" className="btn small">Załóż konto</Link>
        </div>
      </header>
      <main className="wrap">
        <section className="hero">
          <h1>Cały klub w jednym systemie — od DM do bramki.</h1>
          <p className="soft" style={{ fontSize: '1.15rem', maxWidth: 680 }}>
            Bilety z BLIK-iem, loże z przedpłatą, listy gości, promotorzy i skaner offline. Zamiast telefonu, Excela, kartki na bramce i czterech platform naraz.
          </p>
          <div className="row" style={{ marginTop: 20 }}>
            <Link href="/rejestracja" className="btn">Zacznij za darmo</Link>
            <span className="muted">Plan Start: 0 zł abonamentu, płacisz tylko od sprzedaży online.</span>
          </div>
        </section>
        <div className="grid grid-3">
          {FEATURES.map(([h, p]) => (
            <div key={h} className="card"><h3>{h}</h3><p className="soft" style={{ margin: 0 }}>{p}</p></div>
          ))}
        </div>
        <h2 style={{ marginTop: 40 }}>Cennik</h2>
        <div className="grid grid-3">
          {(Object.keys(PLANS) as (keyof typeof PLANS)[]).map((k) => {
            const p = PLANS[k];
            return (
              <div key={k} className={`plan ${k === 'klub' ? 'featured' : ''}`}>
                <h3>{p.label}</h3>
                <div className="price">{p.monthly ? zl(p.monthly) : '0 zł'}<span className="muted" style={{ fontSize: '1rem', fontWeight: 400 }}> /mies.</span></div>
                <p className="soft">bilety {p.ticketPct}% (min. {zl(p.minTicketFee)}), loże {p.loungePct}%{p.extraVenueMonthly ? `; kolejny lokal ${zl(p.extraVenueMonthly)}` : ''}</p>
                <ul>{p.features.map((f) => <li key={f}>{f}</li>)}</ul>
              </div>
            );
          })}
        </div>
        <p className="muted" style={{ marginTop: 12 }}>Opłaty zawierają koszty płatności. Klub decyduje, czy opłatę płaci kupujący, czy klub.</p>
      </main>
      <footer className="site"><Link href="/regulamin">Regulamin</Link> · <Link href="/prywatnosc">Prywatność</Link></footer>
    </>
  );
}
