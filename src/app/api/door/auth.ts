import { cookies } from 'next/headers';
import { one } from '@/lib/db';
import { SESSION_COOKIE } from '@/lib/session';
import { doorTokenValid } from '@/lib/services/door';
import { userForSession } from '@/lib/services/users';

/** Telefon bramki: token z linku (Authorization: Bearer) albo zalogowana osoba z zespołu klubu. */
export async function authorizeDoor(req: Request, eventId: string): Promise<boolean> {
  if (!/^[0-9a-f-]{36}$/i.test(eventId)) return false;
  const auth = req.headers.get('authorization') ?? '';
  if (auth.startsWith('Bearer ')) return doorTokenValid(eventId, auth.slice(7).trim());
  const user = await userForSession((await cookies()).get(SESSION_COOKIE)?.value);
  if (!user) return false;
  return !!(await one(
    `select 1 from events e join memberships m on m.org_id = e.org_id where e.id = $1 and m.user_id = $2`,
    [eventId, user.id],
  ));
}

export const noStore = { 'Cache-Control': 'no-store' };
