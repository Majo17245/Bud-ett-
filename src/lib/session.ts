import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { membership, userForSession, type Role } from './services/users';

export const SESSION_COOKIE = 'sid';

export async function setSessionCookie(token: string) {
  (await cookies()).set(SESSION_COOKIE, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    path: '/',
    maxAge: 60 * 60 * 24 * 30,
  });
}

export async function currentUser() {
  return userForSession((await cookies()).get(SESSION_COOKIE)?.value);
}

export async function requireUser() {
  const user = await currentUser();
  if (!user) redirect('/logowanie');
  return user;
}

/** Sprawdza, czy zalogowana osoba należy do klubu i ma jedną z ról. */
export async function requireOrg(orgSlug: string, roles: Role[] = ['owner', 'manager']) {
  const user = await requireUser();
  const org = await membership(user.id, orgSlug);
  if (!org) redirect('/panel');
  if (!roles.includes(org.role)) redirect(`/panel/${orgSlug}?blad=${encodeURIComponent('Brak uprawnień do tej części panelu.')}`);
  return { user, org };
}

const SECRET_FLASH = 'flash_secret';

/**
 * Jednorazowe pokazanie sekretu (link promotora, hasło tymczasowe) bez umieszczania go w adresie URL,
 * który trafiłby do historii przeglądarki i logów serwera.
 */
export type SecretScope = 'promotorzy' | 'ustawienia' | 'bramka';

export async function setSecretFlash(scope: SecretScope, value: string) {
  (await cookies()).set(SECRET_FLASH, JSON.stringify({ scope, value }), { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'strict', path: '/panel', maxAge: 120 });
}

/** Sekret pokazujemy tylko na stronie, na której powstał (link bramki nie pojawi się w ustawieniach). */
export async function readSecretFlash(scope: SecretScope): Promise<string | null> {
  const raw = (await cookies()).get(SECRET_FLASH)?.value;
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as { scope?: string; value?: string };
    return parsed.scope === scope && typeof parsed.value === 'string' ? parsed.value : null;
  } catch {
    return null;
  }
}
