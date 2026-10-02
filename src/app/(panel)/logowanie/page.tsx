import Link from 'next/link';
import { redirect } from 'next/navigation';
import { Flash } from '@/components/Flash';
import { currentUser } from '@/lib/session';
import { loginAction } from '../actions';

export const metadata = { title: 'Logowanie' };

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ ok?: string; blad?: string }> }) {
  if (await currentUser()) redirect('/panel');
  const sp = await searchParams;
  return (
    <main className="narrow">
      <Link href="/" className="brand">klub<span>owy</span></Link>
      <h1 style={{ marginTop: 24 }}>Logowanie do panelu</h1>
      <Flash sp={sp} />
      <form action={loginAction} className="card">
        <div className="field"><label htmlFor="email">E-mail</label><input id="email" name="email" type="email" autoComplete="email" required /></div>
        <div className="field"><label htmlFor="password">Hasło</label><input id="password" name="password" type="password" autoComplete="current-password" required /></div>
        <button className="block" type="submit">Zaloguj</button>
      </form>
      <p className="soft">Nie masz konta? <Link href="/rejestracja">Załóż konto klubu</Link></p>
      <p className="muted" style={{ fontSize: '.85rem' }}>Ochrona na bramce nie potrzebuje konta — dostaje link do skanera od managera.</p>
    </main>
  );
}
