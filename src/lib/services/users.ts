import { one, q, tx, UserError, type Db } from '../db';
import { hashPassword, randomToken, sha256, verifyPassword } from '../crypto';

export type User = { id: string; email: string; name: string };
export type Role = 'owner' | 'manager' | 'door';

const SESSION_DAYS = 30;
const MAX_FAILED_LOGINS = 8;

export function validatePassword(pw: string) {
  if (pw.length < 10) throw new UserError('Hasło musi mieć co najmniej 10 znaków.');
}

export async function createUser(email: string, name: string, password: string, db?: Db): Promise<User> {
  email = email.trim().toLowerCase();
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) throw new UserError('Podaj poprawny adres e-mail.');
  if (!name.trim()) throw new UserError('Podaj imię i nazwisko.');
  validatePassword(password);
  const exists = await one('select 1 from users where lower(email) = $1', [email], db);
  if (exists) throw new UserError('Konto z tym adresem już istnieje.');
  const hash = await hashPassword(password);
  const row = await one<User>(
    'insert into users (email, name, password_hash) values ($1, $2, $3) returning id, email, name',
    [email, name.trim(), hash], db,
  );
  return row!;
}

/** Zwraca token sesji (do ciasteczka) albo rzuca UserError. */
export async function login(email: string, password: string): Promise<{ token: string; user: User }> {
  email = email.trim().toLowerCase();
  const failed = await one<{ n: string }>(
    `select count(*) as n from login_attempts where lower(email) = $1 and not ok and at > now() - interval '15 minutes'`,
    [email],
  );
  if (Number(failed?.n ?? 0) >= MAX_FAILED_LOGINS) {
    throw new UserError('Za dużo nieudanych prób. Spróbuj ponownie za 15 minut.');
  }
  const user = await one<User & { password_hash: string }>(
    'select id, email, name, password_hash from users where lower(email) = $1', [email],
  );
  const ok = !!user && (await verifyPassword(password, user.password_hash));
  await q('insert into login_attempts (email, ok) values ($1, $2)', [email, ok]);
  if (!ok || !user) throw new UserError('Nieprawidłowy e-mail lub hasło.');
  const token = await createSession(user.id);
  return { token, user: { id: user.id, email: user.email, name: user.name } };
}

export async function createSession(userId: string, db?: Db): Promise<string> {
  const token = randomToken(32);
  await q(
    `insert into sessions (token_hash, user_id, expires_at) values ($1, $2, now() + make_interval(days => $3))`,
    [sha256(token), userId, SESSION_DAYS], db,
  );
  return token;
}

export async function userForSession(token: string | undefined): Promise<User | null> {
  if (!token) return null;
  return one<User>(
    `select u.id, u.email, u.name from sessions s join users u on u.id = s.user_id
     where s.token_hash = $1 and s.expires_at > now()`,
    [sha256(token)],
  );
}

export async function destroySession(token: string | undefined) {
  if (token) await q('delete from sessions where token_hash = $1', [sha256(token)]);
}

export type OrgRow = {
  id: string; slug: string; name: string; kind: 'club' | 'organizer'; city: string | null; address: string | null;
  capacity: number | null; plan: 'start' | 'klub' | 'premium'; fee_payer: 'buyer' | 'org';
  payment_provider: 'none' | 'mock' | 'przelewy24'; p24_merchant_id: number | null; p24_pos_id: number | null;
  p24_sandbox: boolean; contact_email: string | null; instagram: string | null;
};

export const ORG_COLUMNS = `o.id, o.slug, o.name, o.kind, o.city, o.address, o.capacity, o.plan, o.fee_payer,
  o.payment_provider, o.p24_merchant_id, o.p24_pos_id, o.p24_sandbox, o.contact_email, o.instagram`;

export async function membershipsFor(userId: string) {
  return q<OrgRow & { role: Role }>(
    `select ${ORG_COLUMNS}, m.role from memberships m join orgs o on o.id = m.org_id where m.user_id = $1 order by o.name`,
    [userId],
  );
}

export async function membership(userId: string, orgSlug: string) {
  return one<OrgRow & { role: Role }>(
    `select ${ORG_COLUMNS}, m.role from memberships m join orgs o on o.id = m.org_id where m.user_id = $1 and o.slug = $2`,
    [userId, orgSlug],
  );
}

export function slugify(s: string, max = 40): string {
  return s
    .toLowerCase()
    .replace(/ł/g, 'l')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, max)
    .replace(/-+$/g, '');
}

export async function createOrg(userId: string, input: { name: string; kind: 'club' | 'organizer'; city?: string; slug?: string }) {
  const name = input.name.trim();
  if (name.length < 2) throw new UserError('Podaj nazwę klubu.');
  let slug = slugify(input.slug || name);
  if (slug.length < 2) slug = 'klub-' + randomToken(3).toLowerCase().replace(/[^a-z0-9]/g, '');
  return tx(async (c) => {
    let candidate = slug;
    for (let i = 2; await one('select 1 from orgs where slug = $1', [candidate], c); i++) candidate = `${slug}-${i}`;
    const org = await one<{ id: string; slug: string }>(
      `insert into orgs (slug, name, kind, city) values ($1, $2, $3, $4) returning id, slug`,
      [candidate, name, input.kind, input.city?.trim() || null], c,
    );
    await q(`insert into memberships (org_id, user_id, role) values ($1, $2, 'owner')`, [org!.id, userId], c);
    return org!;
  });
}

export async function addMember(orgId: string, email: string, name: string, role: Role) {
  email = email.trim().toLowerCase();
  return tx(async (c) => {
    let user = await one<User>('select id, email, name from users where lower(email) = $1', [email], c);
    let tempPassword: string | null = null;
    if (!user) {
      tempPassword = randomToken(9);
      user = await createUser(email, name || email, tempPassword, c);
    }
    await q(
      `insert into memberships (org_id, user_id, role) values ($1, $2, $3)
       on conflict (org_id, user_id) do update set role = excluded.role`,
      [orgId, user.id, role], c,
    );
    return { user, tempPassword };
  });
}
