'use server';

import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { act, str } from '@/lib/forms';
import { SESSION_COOKIE, requireUser, setSessionCookie } from '@/lib/session';
import { createOrg, createSession, createUser, destroySession, login } from '@/lib/services/users';
import { UserError } from '@/lib/db';

export async function loginAction(fd: FormData) {
  await act('/logowanie', async () => {
    const { token } = await login(str(fd, 'email'), str(fd, 'password'));
    await setSessionCookie(token);
    return { to: '/panel' };
  });
}

export async function registerAction(fd: FormData) {
  await act('/rejestracja', async () => {
    if (fd.get('terms') !== 'on') throw new UserError('Zaakceptuj regulamin usługi.');
    // Nazwę klubu sprawdzamy przed założeniem konta, żeby błąd nie zostawił konta bez klubu.
    if (str(fd, 'orgName').length < 2) throw new UserError('Podaj nazwę klubu.');
    const user = await createUser(str(fd, 'email'), str(fd, 'name'), str(fd, 'password'));
    const org = await createOrg(user.id, { name: str(fd, 'orgName'), kind: str(fd, 'kind') === 'organizer' ? 'organizer' : 'club', city: str(fd, 'city') });
    await setSessionCookie(await createSession(user.id));
    return { to: `/panel/${org.slug}`, ok: 'Konto gotowe. Dodaj pierwszą imprezę.' };
  });
}

export async function logoutAction() {
  const jar = await cookies();
  await destroySession(jar.get(SESSION_COOKIE)?.value);
  jar.delete(SESSION_COOKIE);
  redirect('/logowanie');
}

export async function createOrgAction(fd: FormData) {
  const user = await requireUser();
  await act('/panel', async () => {
    const org = await createOrg(user.id, { name: str(fd, 'orgName'), kind: str(fd, 'kind') === 'organizer' ? 'organizer' : 'club', city: str(fd, 'city') });
    return { to: `/panel/${org.slug}`, ok: 'Klub dodany.' };
  });
}
