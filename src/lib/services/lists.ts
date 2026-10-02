import type { PoolClient } from 'pg';
import { one, q, tx, UserError } from '../db';
import { nameKey, newEntryCode, normalizePhone } from '../crypto';
import { upsertGuest } from './guests';

export type GuestList = {
  id: string; event_id: string; name: string; promoter_id: string | null; capacity: number; entry_until: Date | null;
  promoter_name: string | null; used: number; entered: number;
};

export type GuestEntry = {
  id: string; list_id: string; full_name: string; phone: string | null; email: string | null; plus_ones: number;
  code: string; status: 'invited' | 'void'; checked_in_at: Date | null; created_at: Date;
};

export async function createList(eventId: string, input: { name: string; capacity: number | null; promoterId?: string | null; entryUntil?: Date | null }) {
  if (!input.name?.trim()) throw new UserError('Podaj nazwę listy, np. „Lista DJ-a” albo „Urodziny Ani”.');
  if (!input.capacity || input.capacity < 1) throw new UserError('Podaj limit osób na liście.');
  return one<{ id: string }>(
    `insert into guest_lists (event_id, name, capacity, promoter_id, entry_until) values ($1, $2, $3, $4, $5) returning id`,
    [eventId, input.name.trim(), input.capacity, input.promoterId || null, input.entryUntil ?? null],
  );
}

export async function updateList(eventId: string, listId: string, input: { capacity: number | null; entryUntil: Date | null }) {
  if (!input.capacity || input.capacity < 1) throw new UserError('Podaj limit osób na liście.');
  const used = await one<{ n: number }>(
    `select coalesce(sum(1 + plus_ones), 0)::int as n from guest_entries where list_id = $1 and status = 'invited'`, [listId],
  );
  if (input.capacity < (used?.n ?? 0)) throw new UserError(`Na liście jest już ${used?.n} osób — limit nie może być mniejszy.`);
  await q('update guest_lists set capacity = $3, entry_until = $4 where id = $2 and event_id = $1', [eventId, listId, input.capacity, input.entryUntil]);
}

export async function listsForEvent(eventId: string, promoterId?: string) {
  return q<GuestList>(
    `select l.id, l.event_id, l.name, l.promoter_id, l.capacity, l.entry_until, p.name as promoter_name,
       coalesce((select sum(1 + g.plus_ones) from guest_entries g where g.list_id = l.id and g.status = 'invited'), 0)::int as used,
       coalesce((select sum(1 + g.plus_ones) from guest_entries g where g.list_id = l.id and g.status = 'invited' and g.checked_in_at is not null), 0)::int as entered
     from guest_lists l left join promoters p on p.id = l.promoter_id
     where l.event_id = $1 ${promoterId ? 'and l.promoter_id = $2' : ''} order by l.created_at`,
    promoterId ? [eventId, promoterId] : [eventId],
  );
}

export async function entriesForList(listId: string) {
  return q<GuestEntry>(
    `select id, list_id, full_name, phone, email, plus_ones, code, status, checked_in_at, created_at
     from guest_entries where list_id = $1 order by status, full_name`,
    [listId],
  );
}

export type NewGuest = { fullName: string; plusOnes?: number; phone?: string | null; email?: string | null };

/** "Jan Kowalski +2" → { fullName: "Jan Kowalski", plusOnes: 2 } */
export function parseGuestLine(line: string): NewGuest | null {
  const m = line.trim().match(/^(.*?)(?:\s*\+\s*(\d{1,2}))?\s*$/);
  const name = m?.[1]?.replace(/\s+/g, ' ').trim();
  if (!name) return null;
  return { fullName: name, plusOnes: m?.[2] ? Number(m[2]) : 0 };
}

/**
 * Dodaje gości do listy w jednej transakcji. Pilnuje limitu listy i blokuje
 * duplikaty w obrębie całej imprezy — jedna osoba nie wejdzie z dwóch list.
 */
export async function addGuests(listId: string, guests: NewGuest[], createdBy: string, opts: { promoterId?: string } = {}) {
  if (!guests.length) throw new UserError('Wpisz co najmniej jedno nazwisko.');
  if (guests.length > 500) throw new UserError('Jednorazowo można dodać do 500 osób.');
  return tx(async (c) => {
    const list = await one<{ id: string; event_id: string; capacity: number; promoter_id: string | null; name: string; org_id: string; status: string }>(
      `select l.*, e.org_id, e.status from guest_lists l join events e on e.id = l.event_id where l.id = $1 for update of l`, [listId], c,
    );
    if (!list) throw new UserError('Nie ma takiej listy.');
    if (opts.promoterId && list.promoter_id !== opts.promoterId) throw new UserError('To nie jest Twoja lista.');
    // Blokada na poziomie imprezy: równoległe dopisywanie do dwóch list nie przepuści duplikatu.
    await q('select 1 from events where id = $1 for update', [list.event_id], c);
    const used = await one<{ n: number }>(
      `select coalesce(sum(1 + plus_ones), 0)::int as n from guest_entries where list_id = $1 and status = 'invited'`, [listId], c,
    );
    const adding = guests.reduce((s, g) => s + 1 + (g.plusOnes ?? 0), 0);
    if ((used?.n ?? 0) + adding > list.capacity) {
      throw new UserError(`Limit listy to ${list.capacity} osób, zajęte ${used?.n}. Nie zmieścisz kolejnych ${adding}.`);
    }
    const added: { fullName: string; code: string }[] = [];
    const seenInBatch = new Set<string>();
    for (const g of guests) {
      const fullName = g.fullName.replace(/\s+/g, ' ').trim().slice(0, 120);
      if (fullName.length < 2) throw new UserError('Imię i nazwisko jest za krótkie.');
      const plusOnes = g.plusOnes ?? 0;
      if (!Number.isInteger(plusOnes) || plusOnes < 0 || plusOnes > 20) throw new UserError('Osoby towarzyszące: od 0 do 20.');
      const key = nameKey(fullName);
      if (seenInBatch.has(key)) throw new UserError(`„${fullName}” występuje dwa razy na wklejonej liście.`);
      seenInBatch.add(key);
      const phone = normalizePhone(g.phone);
      await assertNotDuplicate(c, list.event_id, key, phone, fullName);
      const code = newEntryCode('G');
      await q(
        `insert into guest_entries (list_id, event_id, full_name, name_key, phone, email, plus_ones, code, created_by)
         values ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
        [listId, list.event_id, fullName, key, phone, g.email?.trim().toLowerCase() || null, plusOnes, code, createdBy], c,
      );
      if (g.email) await upsertGuest(c, list.org_id, { email: g.email, phone, name: fullName, source: 'lista' });
      added.push({ fullName, code });
    }
    return added;
  });
}

async function assertNotDuplicate(c: PoolClient, eventId: string, key: string, phone: string | null, fullName: string) {
  const dup = await one<{ list_name: string }>(
    `select l.name as list_name from guest_entries g join guest_lists l on l.id = g.list_id
     where g.event_id = $1 and g.status = 'invited' and (g.name_key = $2 or ($3::text is not null and g.phone = $3))
     limit 1`,
    [eventId, key, phone], c,
  );
  if (dup) throw new UserError(`„${fullName}” jest już na liście „${dup.list_name}”.`);
}

export async function voidGuest(eventId: string, entryId: string, opts: { promoterId?: string } = {}) {
  await q(
    `update guest_entries g set status = 'void' from guest_lists l
     where g.id = $2 and g.event_id = $1 and l.id = g.list_id and g.checked_in_at is null
       ${opts.promoterId ? 'and l.promoter_id = $3' : ''}`,
    opts.promoterId ? [eventId, entryId, opts.promoterId] : [eventId, entryId],
  );
}

export async function guestByCode(code: string) {
  if (!/^G[0-9A-Z]{11}$/.test(code)) return null;
  return one<{
    full_name: string; plus_ones: number; code: string; status: string; checked_in_at: Date | null; list_name: string; entry_until: Date | null;
    event_name: string; starts_at: Date; venue_name: string | null; min_age: number | null; org_name: string; org_slug: string; address: string | null;
  }>(
    `select g.full_name, g.plus_ones, g.code, g.status, g.checked_in_at, l.name as list_name, l.entry_until,
            e.name as event_name, e.starts_at, e.venue_name, e.min_age, o.name as org_name, o.slug as org_slug, o.address
     from guest_entries g join guest_lists l on l.id = g.list_id join events e on e.id = g.event_id join orgs o on o.id = e.org_id
     where g.code = $1`,
    [code],
  );
}
