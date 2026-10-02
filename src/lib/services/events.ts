import { one, q, UserError, type Db } from '../db';
import { slugify } from './users';

export type EventRow = {
  id: string; org_id: string; slug: string; name: string; description: string; venue_name: string | null;
  starts_at: Date; ends_at: Date; capacity: number | null; min_age: number | null;
  status: 'draft' | 'published' | 'cancelled';
};

export type TicketTypeRow = {
  id: string; event_id: string; tier_group: string; name: string; price: number; quantity: number;
  group_size: number; sales_start: Date | null; sales_end: Date | null; sort_order: number; active: boolean;
};

export type TicketTypeState = TicketTypeRow & {
  sold: number; held: number; remaining: number;
  state: 'on_sale' | 'sold_out' | 'ended' | 'upcoming' | 'waiting' | 'inactive';
};

const EVENT_COLS = 'id, org_id, slug, name, description, venue_name, starts_at, ends_at, capacity, min_age, status';

export type EventInput = {
  name: string; description?: string; venueName?: string | null; startsAt: Date | null; endsAt: Date | null;
  capacity?: number | null; minAge?: number | null; slug?: string;
};

function validateEvent(input: EventInput) {
  if (!input.name?.trim()) throw new UserError('Podaj nazwę imprezy.');
  if (!input.startsAt || !input.endsAt) throw new UserError('Podaj początek i koniec imprezy.');
  if (input.endsAt <= input.startsAt) throw new UserError('Koniec imprezy musi być po jej początku.');
  if (input.minAge != null && ![16, 18, 21].includes(input.minAge)) throw new UserError('Wiek minimalny: 16, 18 lub 21.');
}

export async function createEvent(orgId: string, input: EventInput, db?: Db): Promise<EventRow> {
  validateEvent(input);
  const base = slugify(input.slug || `${input.name}-${input.startsAt!.toISOString().slice(0, 10)}`, 80) || 'impreza';
  let slug = base;
  for (let i = 2; await one('select 1 from events where org_id = $1 and slug = $2', [orgId, slug], db); i++) slug = `${base}-${i}`;
  const row = await one<EventRow>(
    `insert into events (org_id, slug, name, description, venue_name, starts_at, ends_at, capacity, min_age)
     values ($1, $2, $3, $4, $5, $6, $7, $8, $9) returning ${EVENT_COLS}`,
    [orgId, slug, input.name.trim(), input.description?.trim() ?? '', input.venueName?.trim() || null,
      input.startsAt, input.endsAt, input.capacity ?? null, input.minAge ?? null], db,
  );
  return row!;
}

export async function updateEvent(orgId: string, eventId: string, input: EventInput) {
  validateEvent(input);
  await q(
    `update events set name = $3, description = $4, venue_name = $5, starts_at = $6, ends_at = $7, capacity = $8, min_age = $9
     where id = $1 and org_id = $2`,
    [eventId, orgId, input.name.trim(), input.description?.trim() ?? '', input.venueName?.trim() || null,
      input.startsAt, input.endsAt, input.capacity ?? null, input.minAge ?? null],
  );
}

export async function setEventStatus(orgId: string, eventId: string, status: EventRow['status']) {
  await q('update events set status = $3 where id = $1 and org_id = $2', [eventId, orgId, status]);
}

export async function getEvent(orgId: string, eventId: string, db?: Db) {
  if (!/^[0-9a-f-]{36}$/i.test(eventId)) return null;
  return one<EventRow>(`select ${EVENT_COLS} from events where id = $1 and org_id = $2`, [eventId, orgId], db);
}

export async function listEvents(orgId: string) {
  return q<EventRow & { tickets_sold: string; guests: string; entered: string }>(
    `select ${EVENT_COLS.split(', ').map((c) => 'e.' + c).join(', ')},
       (select count(*) from tickets t where t.event_id = e.id and t.status = 'valid') as tickets_sold,
       (select coalesce(sum(1 + g.plus_ones), 0) from guest_entries g where g.event_id = e.id and g.status = 'invited') as guests,
       (select coalesce(sum(d.persons), 0) from door_events d where d.event_id = e.id and d.type = 'scan' and d.result in ('ok','override')) as entered
     from events e where e.org_id = $1 order by e.starts_at desc`,
    [orgId],
  );
}

export async function publicEvents(orgId: string) {
  return q<EventRow>(
    `select ${EVENT_COLS} from events where org_id = $1 and status = 'published' and ends_at > now() order by starts_at`,
    [orgId],
  );
}

export async function publicEventBySlug(orgSlug: string, eventSlug: string) {
  return one<EventRow & { org_slug: string; org_name: string }>(
    `select ${EVENT_COLS.split(', ').map((c) => 'e.' + c).join(', ')}, o.slug as org_slug, o.name as org_name
     from events e join orgs o on o.id = e.org_id
     where o.slug = $1 and e.slug = $2 and e.status in ('published', 'cancelled')`,
    [orgSlug, eventSlug],
  );
}

// ---------- Pule biletów ----------

export type TicketTypeInput = {
  tierGroup?: string; name: string; price: number | null; quantity: number | null; groupSize?: number | null;
  salesStart?: Date | null; salesEnd?: Date | null; sortOrder?: number | null;
};

export async function addTicketType(eventId: string, input: TicketTypeInput, db?: Db) {
  if (!input.name?.trim()) throw new UserError('Podaj nazwę puli, np. "Early bird".');
  if (input.price == null || input.price < 0) throw new UserError('Podaj cenę (0 = bezpłatne).');
  if (input.quantity == null || input.quantity < 0) throw new UserError('Podaj liczbę biletów w puli.');
  const groupSize = input.groupSize ?? 1;
  if (groupSize < 1 || groupSize > 20) throw new UserError('Bilet grupowy: od 1 do 20 osób.');
  let sortOrder = input.sortOrder;
  if (sortOrder == null) {
    const r = await one<{ n: number }>('select coalesce(max(sort_order), 0) + 10 as n from ticket_types where event_id = $1', [eventId], db);
    sortOrder = r!.n;
  }
  return one<TicketTypeRow>(
    `insert into ticket_types (event_id, tier_group, name, price, quantity, group_size, sales_start, sales_end, sort_order)
     values ($1, $2, $3, $4, $5, $6, $7, $8, $9) returning *`,
    [eventId, input.tierGroup?.trim() || 'Wejście', input.name.trim(), input.price, input.quantity, groupSize,
      input.salesStart ?? null, input.salesEnd ?? null, sortOrder], db,
  );
}

export async function setTicketTypeActive(eventId: string, ticketTypeId: string, active: boolean) {
  await q('update ticket_types set active = $3 where id = $2 and event_id = $1', [eventId, ticketTypeId, active]);
}

export async function updateTicketTypeQuantity(eventId: string, ticketTypeId: string, quantity: number) {
  const sold = await one<{ n: number }>(
    `select coalesce(sum(oi.quantity), 0)::int as n from order_items oi join orders o on o.id = oi.order_id
     where oi.ticket_type_id = $1 and (o.status = 'paid' or (o.status = 'pending' and o.expires_at > now()))`,
    [ticketTypeId],
  );
  if (quantity < (sold?.n ?? 0)) throw new UserError(`Sprzedano już ${sold?.n} szt. — pula nie może być mniejsza.`);
  await q('update ticket_types set quantity = $3 where id = $2 and event_id = $1', [eventId, ticketTypeId, quantity]);
}

/**
 * Stan pul z policzonymi wolnymi miejscami. Zamówienia oczekujące na płatność
 * blokują bilety do czasu wygaśnięcia (expires_at).
 */
export async function ticketTypesWithState(eventId: string, db?: Db, opts: { forUpdate?: boolean; now?: Date } = {}): Promise<TicketTypeState[]> {
  const rows = await q<TicketTypeRow>(
    `select * from ticket_types where event_id = $1 order by sort_order, id ${opts.forUpdate ? 'for update' : ''}`,
    [eventId], db,
  );
  if (!rows.length) return [];
  const counts = await q<{ ticket_type_id: string; sold: number; held: number }>(
    `select oi.ticket_type_id,
       coalesce(sum(oi.quantity) filter (where o.status = 'paid'), 0)::int as sold,
       coalesce(sum(oi.quantity) filter (where o.status = 'pending' and o.expires_at > now()), 0)::int as held
     from order_items oi join orders o on o.id = oi.order_id
     where oi.ticket_type_id = any($1::uuid[]) group by oi.ticket_type_id`,
    [rows.map((r) => r.id)], db,
  );
  const byId = new Map(counts.map((c) => [c.ticket_type_id, c]));
  const now = opts.now ?? new Date();
  const result: TicketTypeState[] = rows.map((r) => {
    const c = byId.get(r.id);
    const sold = c?.sold ?? 0;
    const held = c?.held ?? 0;
    const remaining = Math.max(0, r.quantity - sold - held);
    let state: TicketTypeState['state'];
    if (!r.active) state = 'inactive';
    else if (r.sales_end && r.sales_end <= now) state = 'ended';
    else if (remaining <= 0) state = 'sold_out';
    else if (r.sales_start && r.sales_start > now) state = 'upcoming';
    else state = 'on_sale';
    return { ...r, sold, held, remaining, state };
  });
  // W każdej grupie w sprzedaży jest tylko pierwsza dostępna pula; kolejne czekają na swoją kolej.
  const seen = new Set<string>();
  for (const t of result) {
    if (t.state !== 'on_sale') continue;
    if (seen.has(t.tier_group)) t.state = 'waiting';
    else seen.add(t.tier_group);
  }
  return result;
}
