import { one, q, type Db } from '../db';

/** Dopisuje lub aktualizuje gościa w bazie klubu. Zgoda marketingowa tylko się "włącza", nigdy nie jest wyłączana automatycznie. */
export async function upsertGuest(db: Db, orgId: string, g: {
  email?: string | null; phone?: string | null; name?: string | null; consent?: boolean; source: string; spent?: number; order?: boolean;
}) {
  const email = g.email?.trim().toLowerCase() || null;
  if (!email) return null;
  const row = await one<{ id: string }>(
    `insert into guests (org_id, email, phone, name, marketing_consent, consent_at, consent_source, orders_count, total_spent)
     values ($1, $2, $3, $4, $5, case when $5 then now() end, case when $5 then $6 end, $7, $8)
     on conflict (org_id, lower(email)) where email is not null do update set
       phone = coalesce(excluded.phone, guests.phone),
       name = coalesce(excluded.name, guests.name),
       marketing_consent = guests.marketing_consent or excluded.marketing_consent,
       consent_at = case when not guests.marketing_consent and excluded.marketing_consent then now() else guests.consent_at end,
       consent_source = case when not guests.marketing_consent and excluded.marketing_consent then excluded.consent_source else guests.consent_source end,
       orders_count = guests.orders_count + excluded.orders_count,
       total_spent = guests.total_spent + excluded.total_spent,
       last_seen_at = now()
     returning id`,
    [orgId, email, g.phone || null, g.name || null, !!g.consent, g.source, g.order ? 1 : 0, g.spent ?? 0], db,
  );
  return row?.id ?? null;
}

export async function listGuests(orgId: string, opts: { search?: string; consentOnly?: boolean; limit?: number } = {}) {
  const params: unknown[] = [orgId];
  let where = 'org_id = $1 and anonymized_at is null';
  if (opts.consentOnly) where += ' and marketing_consent';
  if (opts.search) {
    params.push('%' + opts.search.toLowerCase() + '%');
    where += ` and (lower(coalesce(name,'')) like $${params.length} or lower(coalesce(email,'')) like $${params.length} or coalesce(phone,'') like $${params.length})`;
  }
  params.push(opts.limit ?? 200);
  return q<{ id: string; email: string | null; phone: string | null; name: string | null; marketing_consent: boolean; consent_at: Date | null; orders_count: number; total_spent: number; last_seen_at: Date }>(
    `select id, email, phone, name, marketing_consent, consent_at, orders_count, total_spent, last_seen_at
     from guests where ${where} order by last_seen_at desc limit $${params.length}`,
    params,
  );
}

export async function guestStats(orgId: string) {
  return one<{ total: string; consent: string }>(
    `select count(*) as total, count(*) filter (where marketing_consent) as consent from guests where org_id = $1 and anonymized_at is null`,
    [orgId],
  );
}

/** Prawo do usunięcia danych (RODO): anonimizujemy, zostawiając statystyki. */
export async function anonymizeGuest(orgId: string, guestId: string) {
  await q(
    `update guests set email = null, phone = null, name = null, marketing_consent = false, anonymized_at = now()
     where id = $1 and org_id = $2`,
    [guestId, orgId],
  );
}
