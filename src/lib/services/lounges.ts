import { one, q, tx, UserError } from '../db';
import { newEntryCode, normalizePhone } from '../crypto';
import { loungePrice } from '../pricing';
import { assertLoungeFree } from './orders';

export type Lounge = {
  id: string; org_id: string; name: string; zone: string; capacity: number; max_capacity: number; base_price: number;
  extra_person_price: number; min_spend: number; prepay_percent: number; map_x: string; map_y: string; map_w: string; map_h: string;
  sort_order: number; active: boolean;
};

export type LoungeInput = {
  name: string; zone?: string; capacity: number | null; maxCapacity: number | null; basePrice: number | null;
  extraPersonPrice?: number | null; minSpend?: number | null; prepayPercent?: number | null;
  mapX?: number | null; mapY?: number | null; mapW?: number | null; mapH?: number | null;
};

function validate(i: LoungeInput) {
  if (!i.name?.trim()) throw new UserError('Podaj nazwę loży.');
  if (!i.capacity || i.capacity < 1) throw new UserError('Podaj liczbę osób w cenie loży.');
  if (!i.maxCapacity || i.maxCapacity < i.capacity) throw new UserError('Maksymalna liczba osób nie może być mniejsza niż liczba osób w cenie.');
  if (i.basePrice == null || i.basePrice < 0) throw new UserError('Podaj cenę loży.');
  if (i.prepayPercent != null && (i.prepayPercent < 0 || i.prepayPercent > 100)) throw new UserError('Przedpłata: od 0 do 100%.');
}

const clampPct = (v: number | null | undefined, d: number) => Math.min(100, Math.max(0, v ?? d));

export async function createLounge(orgId: string, i: LoungeInput) {
  validate(i);
  return one<{ id: string }>(
    `insert into lounges (org_id, name, zone, capacity, max_capacity, base_price, extra_person_price, min_spend, prepay_percent,
       map_x, map_y, map_w, map_h, sort_order)
     values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
       (select coalesce(max(sort_order), 0) + 10 from lounges where org_id = $1)) returning id`,
    [orgId, i.name.trim(), i.zone?.trim() || 'Sala główna', i.capacity, i.maxCapacity, i.basePrice, i.extraPersonPrice ?? 0,
      i.minSpend ?? 0, i.prepayPercent ?? 50, clampPct(i.mapX, 10), clampPct(i.mapY, 10), clampPct(i.mapW, 14), clampPct(i.mapH, 12)],
  );
}

export async function updateLounge(orgId: string, id: string, i: LoungeInput) {
  validate(i);
  await q(
    `update lounges set name = $3, zone = $4, capacity = $5, max_capacity = $6, base_price = $7, extra_person_price = $8,
       min_spend = $9, prepay_percent = $10, map_x = $11, map_y = $12, map_w = $13, map_h = $14
     where id = $1 and org_id = $2`,
    [id, orgId, i.name.trim(), i.zone?.trim() || 'Sala główna', i.capacity, i.maxCapacity, i.basePrice, i.extraPersonPrice ?? 0,
      i.minSpend ?? 0, i.prepayPercent ?? 50, clampPct(i.mapX, 10), clampPct(i.mapY, 10), clampPct(i.mapW, 14), clampPct(i.mapH, 12)],
  );
}

export async function setLoungeActive(orgId: string, id: string, active: boolean) {
  await q('update lounges set active = $3 where id = $1 and org_id = $2', [id, orgId, active]);
}

export async function loungesForOrg(orgId: string, activeOnly = false) {
  return q<Lounge>(`select * from lounges where org_id = $1 ${activeOnly ? 'and active' : ''} order by sort_order, name`, [orgId]);
}

/** Loże z informacją, czy są wolne na daną noc (do mapy sali na stronie imprezy). */
export async function loungeAvailability(orgId: string, eventId: string) {
  return q<Lounge & { taken: boolean; pending_requests: number }>(
    `select l.*,
       exists (select 1 from lounge_reservations r where r.event_id = $2 and r.lounge_id = l.id
               and (r.status in ('confirmed', 'paid') or (r.status = 'pending_payment' and r.hold_until > now()))) as taken,
       (select count(*) from lounge_reservations r where r.event_id = $2 and r.lounge_id = l.id and r.status = 'requested')::int as pending_requests
     from lounges l where l.org_id = $1 and l.active order by l.sort_order, l.name`,
    [orgId, eventId],
  );
}

export type ReservationRow = {
  id: string; lounge_id: string; lounge_name: string; status: string; name: string; phone: string | null; email: string | null;
  persons: number; total_price: number; prepay_amount: number; source: string; notes: string | null; code: string;
  checked_in_at: Date | null; created_at: Date; promoter_name: string | null;
};

export async function reservationsForEvent(eventId: string) {
  return q<ReservationRow>(
    `select r.id, r.lounge_id, l.name as lounge_name, r.status, r.name, r.phone, r.email, r.persons, r.total_price, r.prepay_amount,
            r.source, r.notes, r.code, r.checked_in_at, r.created_at, p.name as promoter_name
     from lounge_reservations r join lounges l on l.id = r.lounge_id left join promoters p on p.id = r.promoter_id
     where r.event_id = $1 and not (r.status = 'pending_payment' and r.hold_until <= now())
     order by l.sort_order, r.created_at`,
    [eventId],
  );
}

/** Rezerwacja przyjęta przez telefon / DM — od razu potwierdzona. */
export async function addManualReservation(orgId: string, eventId: string, i: {
  loungeId: string; name: string; phone?: string | null; persons: number; source: 'phone' | 'dm' | 'panel'; notes?: string | null;
}) {
  if (!i.name?.trim()) throw new UserError('Podaj nazwisko gościa.');
  return tx(async (c) => {
    const lounge = await one<Lounge>('select * from lounges where id = $1 and org_id = $2 for update', [i.loungeId, orgId], c);
    if (!lounge) throw new UserError('Nie ma takiej loży.');
    await assertLoungeFree(c, eventId, lounge.id);
    let price;
    try {
      price = loungePrice(lounge, i.persons);
    } catch (e) {
      throw new UserError((e as Error).message);
    }
    return one<{ id: string; code: string }>(
      `insert into lounge_reservations (event_id, lounge_id, status, name, phone, persons, total_price, prepay_amount, source, notes, code)
       values ($1, $2, 'confirmed', $3, $4, $5, $6, 0, $7, $8, $9) returning id, code`,
      [eventId, lounge.id, i.name.trim(), normalizePhone(i.phone), i.persons, price.total, i.source, i.notes?.trim() || null, newEntryCode('L')], c,
    );
  });
}

export async function setReservationStatus(eventId: string, reservationId: string, status: 'confirmed' | 'cancelled' | 'no_show') {
  return tx(async (c) => {
    const r = await one<{ lounge_id: string; status: string }>(
      'select lounge_id, status from lounge_reservations where id = $1 and event_id = $2 for update', [reservationId, eventId], c,
    );
    if (!r) throw new UserError('Nie ma takiej rezerwacji.');
    if (status === 'confirmed') {
      if (r.status !== 'requested') throw new UserError('Potwierdzić można tylko prośbę o rezerwację.');
      await one('select 1 from lounges where id = $1 for update', [r.lounge_id], c);
      await assertLoungeFree(c, eventId, r.lounge_id, reservationId);
    }
    if (status === 'cancelled' && r.status === 'paid') {
      throw new UserError('Rezerwacja jest opłacona — najpierw zwróć przedpłatę u operatora płatności, potem ją anuluj.');
    }
    await q('update lounge_reservations set status = $2 where id = $1', [reservationId, status], c);
  });
}
