import { one, q, UserError } from '../db';
import { randomToken, sha256 } from '../crypto';

export type Promoter = {
  id: string; org_id: string; name: string; code: string; phone: string | null; email: string | null;
  ticket_commission_pct: string; guest_commission: number; active: boolean;
};

export async function createPromoter(orgId: string, i: {
  name: string; code?: string; phone?: string | null; email?: string | null; ticketCommissionPct?: number | null; guestCommission?: number | null;
}) {
  if (!i.name?.trim()) throw new UserError('Podaj imię promotora.');
  const base = (i.code?.trim() || i.name.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/gi, 'L'))
    .toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 12);
  if (base.length < 3) throw new UserError('Kod promotora musi mieć co najmniej 3 litery lub cyfry.');
  let code = base;
  for (let n = 2; await one('select 1 from promoters where org_id = $1 and code = $2', [orgId, code]); n++) code = `${base}${n}`;
  const token = randomToken(24);
  const row = await one<{ id: string }>(
    `insert into promoters (org_id, name, code, phone, email, ticket_commission_pct, guest_commission, panel_token_hash)
     values ($1, $2, $3, $4, $5, $6, $7, $8) returning id`,
    [orgId, i.name.trim(), code, i.phone?.trim() || null, i.email?.trim() || null, i.ticketCommissionPct ?? 0, i.guestCommission ?? 0, sha256(token)],
  );
  return { id: row!.id, code, panelToken: token };
}

export async function regeneratePanelToken(orgId: string, promoterId: string) {
  const token = randomToken(24);
  await q('update promoters set panel_token_hash = $3 where id = $1 and org_id = $2', [promoterId, orgId, sha256(token)]);
  return token;
}

export async function setPromoterActive(orgId: string, promoterId: string, active: boolean) {
  await q('update promoters set active = $3 where id = $1 and org_id = $2', [promoterId, orgId, active]);
}

export async function promotersForOrg(orgId: string) {
  return q<Promoter>('select * from promoters where org_id = $1 order by active desc, name', [orgId]);
}

export async function promoterByToken(token: string) {
  if (!token || token.length < 20) return null;
  return one<Promoter & { org_name: string; org_slug: string }>(
    `select p.*, o.name as org_name, o.slug as org_slug from promoters p join orgs o on o.id = p.org_id
     where p.panel_token_hash = $1 and p.active`,
    [sha256(token)],
  );
}

export type PromoterStats = {
  promoter_id: string; name: string; code: string; tickets: number; ticket_revenue: number; guests_listed: number;
  guests_entered: number; lounges: number; commission: number;
};

/**
 * Wyniki promotorów (dla jednej imprezy albo wszystkich) z wyliczoną prowizją:
 * procent od przychodu z biletów + stała kwota za każdego gościa z listy, który wszedł.
 */
export async function promoterStats(orgId: string, eventId?: string): Promise<PromoterStats[]> {
  const rows = await q<Omit<PromoterStats, 'commission'> & { ticket_commission_pct: string; guest_commission: number }>(
    `select p.id as promoter_id, p.name, p.code, p.ticket_commission_pct, p.guest_commission,
       coalesce((select count(*) from tickets t join orders o on o.id = t.order_id
                 where o.promoter_id = p.id and o.status = 'paid' and t.status = 'valid' ${eventId ? 'and o.event_id = $2' : ''}), 0)::int as tickets,
       coalesce((select sum(o.subtotal) from orders o
                 where o.promoter_id = p.id and o.status = 'paid' and o.kind = 'tickets' ${eventId ? 'and o.event_id = $2' : ''}), 0)::int as ticket_revenue,
       coalesce((select sum(1 + g.plus_ones) from guest_entries g join guest_lists l on l.id = g.list_id
                 where l.promoter_id = p.id and g.status = 'invited' ${eventId ? 'and g.event_id = $2' : ''}), 0)::int as guests_listed,
       coalesce((select sum(1 + g.plus_ones) from guest_entries g join guest_lists l on l.id = g.list_id
                 where l.promoter_id = p.id and g.status = 'invited' and g.checked_in_at is not null ${eventId ? 'and g.event_id = $2' : ''}), 0)::int as guests_entered,
       coalesce((select count(*) from lounge_reservations r
                 where r.promoter_id = p.id and r.status in ('confirmed', 'paid') ${eventId ? 'and r.event_id = $2' : ''}), 0)::int as lounges
     from promoters p where p.org_id = $1`,
    eventId ? [orgId, eventId] : [orgId],
  );
  return rows
    .map(({ ticket_commission_pct, guest_commission, ...r }) => ({
      ...r,
      commission: Math.round((r.ticket_revenue * Number(ticket_commission_pct)) / 100) + r.guests_entered * guest_commission,
    }))
    .sort((a, b) => b.tickets + b.guests_entered - (a.tickets + a.guests_entered) || b.ticket_revenue - a.ticket_revenue);
}
