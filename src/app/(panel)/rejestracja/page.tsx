import Link from 'next/link';
import { Flash } from '@/components/Flash';
import { registerAction } from '../actions';

export const metadata = { title: 'Załóż konto' };

export default async function RegisterPage({ searchParams }: { searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const sp = await searchParams;
  return (
    <main className="narrow">
      <Link href="/" className="brand">klub<span>owy</span></Link>
      <h1 style={{ marginTop: 24 }}>Załóż konto klubu</h1>
      <p className="soft">Plan Start jest bezpłatny: płacisz tylko od sprzedaży online.</p>
      <Flash sp={sp} />
      <form action={registerAction} className="card">
        <div className="field"><label htmlFor="orgName">Nazwa klubu lub organizatora</label><input id="orgName" name="orgName" required /></div>
        <div className="form-grid">
          <div className="field">
            <label htmlFor="kind">Rodzaj</label>
            <select id="kind" name="kind"><option value="club">Klub / dyskoteka</option><option value="organizer">Organizator bez lokalu</option></select>
          </div>
          <div className="field"><label htmlFor="city">Miasto</label><input id="city" name="city" /></div>
        </div>
        <hr />
        <div className="field"><label htmlFor="name">Imię i nazwisko</label><input id="name" name="name" autoComplete="name" required /></div>
        <div className="field"><label htmlFor="email">E-mail</label><input id="email" name="email" type="email" autoComplete="email" required /></div>
        <div className="field"><label htmlFor="password">Hasło (min. 10 znaków)</label><input id="password" name="password" type="password" minLength={10} autoComplete="new-password" required /></div>
        <label className="check field"><input type="checkbox" name="terms" required /> <span>Akceptuję <Link href="/regulamin">regulamin usługi</Link> i <Link href="/prywatnosc">zasady przetwarzania danych</Link>.</span></label>
        <button className="block" type="submit">Załóż konto</button>
      </form>
      <p className="soft">Masz już konto? <Link href="/logowanie">Zaloguj się</Link></p>
    </main>
  );
}
