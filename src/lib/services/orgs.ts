import { one, q, UserError } from '../db';
import { encryptSecret } from '../crypto';
import { env } from '../env';
import { ORG_COLUMNS, type OrgRow } from './users';

export async function orgBySlug(slug: string) {
  return one<OrgRow>(`select ${ORG_COLUMNS} from orgs o where o.slug = $1`, [slug]);
}

export async function updateOrgProfile(orgId: string, i: {
  name: string; city?: string | null; address?: string | null; capacity?: number | null; contactEmail?: string | null;
  instagram?: string | null; feePayer: 'buyer' | 'org'; plan: 'start' | 'klub' | 'premium';
}) {
  if (!i.name?.trim()) throw new UserError('Podaj nazwę klubu.');
  if (i.contactEmail && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(i.contactEmail)) throw new UserError('Nieprawidłowy e-mail kontaktowy.');
  await q(
    `update orgs set name = $2, city = $3, address = $4, capacity = $5, contact_email = $6, instagram = $7, fee_payer = $8, plan = $9 where id = $1`,
    [orgId, i.name.trim(), i.city?.trim() || null, i.address?.trim() || null, i.capacity || null, i.contactEmail?.trim() || null,
      i.instagram?.trim().replace(/^@/, '') || null, i.feePayer, i.plan],
  );
}

export async function updatePayments(orgId: string, i: {
  provider: 'none' | 'mock' | 'przelewy24'; merchantId?: number | null; posId?: number | null; crc?: string | null; apiKey?: string | null; sandbox?: boolean;
}) {
  if (i.provider === 'mock' && !env.allowMockPayments) throw new UserError('Płatności testowe są wyłączone na tym serwerze.');
  if (i.provider === 'przelewy24') {
    const current = await one<{ p24_crc_enc: string | null; p24_api_key_enc: string | null }>('select p24_crc_enc, p24_api_key_enc from orgs where id = $1', [orgId]);
    if (!i.merchantId) throw new UserError('Podaj ID sprzedawcy z panelu Przelewy24.');
    if (!i.crc && !current?.p24_crc_enc) throw new UserError('Podaj klucz CRC z panelu Przelewy24.');
    if (!i.apiKey && !current?.p24_api_key_enc) throw new UserError('Podaj klucz do raportów (API) z panelu Przelewy24.');
    await q(
      `update orgs set payment_provider = 'przelewy24', p24_merchant_id = $2, p24_pos_id = $3, p24_sandbox = $4,
         p24_crc_enc = coalesce($5, p24_crc_enc), p24_api_key_enc = coalesce($6, p24_api_key_enc) where id = $1`,
      [orgId, i.merchantId, i.posId || i.merchantId, i.sandbox ?? true, i.crc ? encryptSecret(i.crc.trim()) : null, i.apiKey ? encryptSecret(i.apiKey.trim()) : null],
    );
    return;
  }
  await q('update orgs set payment_provider = $2 where id = $1', [orgId, i.provider]);
}

export async function teamMembers(orgId: string) {
  return q<{ user_id: string; email: string; name: string; role: string }>(
    `select u.id as user_id, u.email, u.name, m.role from memberships m join users u on u.id = m.user_id where m.org_id = $1 order by m.role, u.name`,
    [orgId],
  );
}

export async function removeMember(orgId: string, userId: string) {
  const owners = await one<{ n: number }>(`select count(*)::int as n from memberships where org_id = $1 and role = 'owner' and user_id <> $2`, [orgId, userId]);
  if (!owners?.n) throw new UserError('Klub musi mieć co najmniej jednego właściciela.');
  await q('delete from memberships where org_id = $1 and user_id = $2', [orgId, userId]);
}

export async function discountCodes(orgId: string, eventId: string) {
  return q<{ id: string; code: string; percent_off: number; max_uses: number | null; used: number; active: boolean; event_id: string | null }>(
    'select id, code, percent_off, max_uses, used, active, event_id from discount_codes where org_id = $1 and (event_id = $2 or event_id is null) order by created_at',
    [orgId, eventId],
  );
}

export async function createDiscountCode(orgId: string, eventId: string | null, i: { code: string; percentOff: number | null; maxUses?: number | null }) {
  const code = i.code.trim().toUpperCase();
  if (!/^[A-Z0-9-]{3,24}$/.test(code)) throw new UserError('Kod: 3–24 znaki, litery, cyfry i myślniki.');
  if (!i.percentOff || i.percentOff < 1 || i.percentOff > 100) throw new UserError('Rabat: od 1 do 100%.');
  if (await one('select 1 from discount_codes where org_id = $1 and code = $2', [orgId, code])) throw new UserError('Taki kod już istnieje.');
  await q('insert into discount_codes (org_id, event_id, code, percent_off, max_uses) values ($1, $2, $3, $4, $5)', [orgId, eventId, code, i.percentOff, i.maxUses || null]);
}

export async function setDiscountActive(orgId: string, id: string, active: boolean) {
  await q('update discount_codes set active = $3 where id = $1 and org_id = $2', [id, orgId, active]);
}
