import type { PoolClient } from 'pg';
import { z } from 'zod';
import { one, q, tx, UserError } from '../db';
import { randomToken, sha256 } from '../crypto';

export type RefKind = 'ticket' | 'guest' | 'lounge' | 'external';
export type ScanResult = 'ok' | 'override' | 'duplicate' | 'invalid' | 'void' | 'too_late';

/** Wpis manifestu — telefon bramki trzyma go lokalnie i sprawdza kody bez internetu. */
export type ManifestEntry = {
  c: string;            // kod z QR
  k: RefKind;
  n: string;            // imię i nazwisko / nazwa
  p: number;            // ile osób wchodzi na ten kod
  i: string;            // pula / lista / loża / źródło
  u: string | null;     // wejście tylko do (ISO)
  x: 0 | 1;             // już wszedł
  v: 0 | 1;             // unieważniony
};

export type DoorSummary = { inside: number; entered: number; scans: number; cursor: number };

// ---------- Dostęp telefonów bramki ----------

export async function createDoorToken(eventId: string, label: string) {
  const ev = await one<{ ends_at: Date }>('select ends_at from events where id = $1', [eventId]);
  if (!ev) throw new UserError('Nie ma takiej imprezy.');
  const token = randomToken(24);
  await q(
    `insert into door_tokens (event_id, label, token_hash, expires_at) values ($1, $2, $3, $4::timestamptz + interval '12 hours')`,
    [eventId, label.trim() || 'Bramka', sha256(token), ev.ends_at],
  );
  return token;
}

export async function doorTokens(eventId: string) {
  return q<{ id: string; label: string; created_at: Date; expires_at: Date; revoked_at: Date | null }>(
    'select id, label, created_at, expires_at, revoked_at from door_tokens where event_id = $1 order by created_at', [eventId],
  );
}

export async function revokeDoorToken(eventId: string, tokenId: string) {
  await q('update door_tokens set revoked_at = now() where id = $1 and event_id = $2', [tokenId, eventId]);
}

export async function doorTokenValid(eventId: string, token: string) {
  if (!token) return false;
  return !!(await one(
    'select 1 from door_tokens where event_id = $1 and token_hash = $2 and revoked_at is null and expires_at > now()',
    [eventId, sha256(token)],
  ));
}

// ---------- Manifest ----------

export async function buildManifest(eventId: string) {
  const event = await one<{ id: string; name: string; starts_at: Date; ends_at: Date; capacity: number | null; min_age: number | null; org_name: string; org_capacity: number | null }>(
    `select e.id, e.name, e.starts_at, e.ends_at, e.capacity, e.min_age, o.name as org_name, o.capacity as org_capacity
     from events e join orgs o on o.id = e.org_id where e.id = $1`,
    [eventId],
  );
  if (!event) return null;
  const entries = await q<ManifestEntry>(
    `select t.code as c, 'ticket' as k, o.buyer_name as n, 1 as p, 'Bilet: ' || tt.name as i, null as u,
            (t.checked_in_at is not null)::int as x, (t.status = 'void')::int as v
       from tickets t join ticket_types tt on tt.id = t.ticket_type_id join orders o on o.id = t.order_id where t.event_id = $1
     union all
     select g.code, 'guest', g.full_name, 1 + g.plus_ones, 'Lista: ' || l.name, to_char(l.entry_until at time zone 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
            (g.checked_in_at is not null)::int, (g.status = 'void')::int
       from guest_entries g join guest_lists l on l.id = g.list_id where g.event_id = $1
     union all
     select r.code, 'lounge', r.name, r.persons, 'Loża: ' || lo.name, null,
            (r.checked_in_at is not null)::int, (r.status not in ('confirmed', 'paid'))::int
       from lounge_reservations r join lounges lo on lo.id = r.lounge_id
       where r.event_id = $1 and r.status in ('confirmed', 'paid', 'cancelled', 'no_show')
     union all
     select x.code, 'external', coalesce(x.holder_name, ''), 1, upper(x.source) || coalesce(': ' || x.ticket_label, ''), null,
            (x.checked_in_at is not null)::int, 0
       from external_tickets x where x.event_id = $1`,
    [eventId],
  );
  return { event: { ...event, capacity: event.capacity ?? event.org_capacity }, entries, summary: await doorSummary(eventId), generatedAt: new Date().toISOString() };
}

export async function doorSummary(eventId: string, db?: PoolClient): Promise<DoorSummary> {
  const r = await one<{ inside: number; entered: number; scans: number; cursor: string }>(
    `select
       coalesce(sum(case when type = 'out' then -persons
                         when (type = 'scan' and result in ('ok', 'override')) or type = 'in' then persons else 0 end), 0)::int as inside,
       coalesce(sum(persons) filter (where (type = 'scan' and result in ('ok', 'override')) or type = 'in'), 0)::int as entered,
       count(*) filter (where type = 'scan')::int as scans,
       coalesce(max(id), 0) as cursor
     from door_events where event_id = $1`,
    [eventId], db,
  );
  return { inside: Math.max(0, r!.inside), entered: r!.entered, scans: r!.scans, cursor: Number(r!.cursor) };
}

// ---------- Synchronizacja ----------

export const SyncInput = z.object({
  deviceId: z.string().min(4).max(64),
  cursor: z.number().int().min(0).default(0),
  events: z.array(z.object({
    clientId: z.string().min(8).max(64),
    type: z.enum(['scan', 'in', 'out']),
    code: z.string().max(200).optional(),
    persons: z.number().int().min(1).max(50).optional(),
    override: z.boolean().optional(),
    at: z.string().datetime(),
  })).max(500),
});
export type SyncInput = z.infer<typeof SyncInput>;

type Resolved = {
  kind: RefKind; id: string; persons: number; label: string; until: Date | null; used: boolean; void: boolean; eventId: string;
};

const INTERNAL_CODE = /^[TGL][0-9A-Z]{11}$/;

async function resolveCode(c: PoolClient, eventId: string, raw: string): Promise<Resolved | null> {
  const code = raw.trim();
  const upper = code.toUpperCase();
  if (INTERNAL_CODE.test(upper)) {
    if (upper[0] === 'T') {
      const t = await one<{ id: string; event_id: string; status: string; checked_in_at: Date | null; buyer_name: string; type_name: string }>(
        `select t.id, t.event_id, t.status, t.checked_in_at, o.buyer_name, tt.name as type_name
         from tickets t join orders o on o.id = t.order_id join ticket_types tt on tt.id = t.ticket_type_id where t.code = $1 for update of t`,
        [upper], c,
      );
      if (t) return { kind: 'ticket', id: t.id, persons: 1, label: `${t.buyer_name} · ${t.type_name}`, until: null, used: !!t.checked_in_at, void: t.status === 'void', eventId: t.event_id };
    } else if (upper[0] === 'G') {
      const g = await one<{ id: string; event_id: string; status: string; checked_in_at: Date | null; full_name: string; plus_ones: number; list_name: string; entry_until: Date | null }>(
        `select g.id, g.event_id, g.status, g.checked_in_at, g.full_name, g.plus_ones, l.name as list_name, l.entry_until
         from guest_entries g join guest_lists l on l.id = g.list_id where g.code = $1 for update of g`,
        [upper], c,
      );
      if (g) return { kind: 'guest', id: g.id, persons: 1 + g.plus_ones, label: `${g.full_name} · lista ${g.list_name}`, until: g.entry_until, used: !!g.checked_in_at, void: g.status === 'void', eventId: g.event_id };
    } else {
      const r = await one<{ id: string; event_id: string; status: string; checked_in_at: Date | null; name: string; persons: number; lounge_name: string }>(
        `select r.id, r.event_id, r.status, r.checked_in_at, r.name, r.persons, l.name as lounge_name
         from lounge_reservations r join lounges l on l.id = r.lounge_id where r.code = $1 for update of r`,
        [upper], c,
      );
      if (r) return { kind: 'lounge', id: r.id, persons: r.persons, label: `${r.name} · ${r.lounge_name}`, until: null, used: !!r.checked_in_at, void: !['confirmed', 'paid'].includes(r.status), eventId: r.event_id };
    }
  }
  const x = await one<{ id: string; checked_in_at: Date | null; holder_name: string | null; source: string }>(
    'select id, checked_in_at, holder_name, source from external_tickets where event_id = $1 and code = $2 for update', [eventId, code], c,
  );
  if (x) return { kind: 'external', id: x.id, persons: 1, label: `${x.holder_name ?? 'Bilet'} · ${x.source.toUpperCase()}`, until: null, used: !!x.checked_in_at, void: false, eventId };
  return null;
}

const TABLE: Record<RefKind, string> = { ticket: 'tickets', guest: 'guest_entries', lounge: 'lounge_reservations', external: 'external_tickets' };

/** Czas z telefonu, ale w rozsądnych granicach (zegar urządzenia bywa przestawiony). */
function clampTime(iso: string): Date {
  const t = new Date(iso);
  const now = Date.now();
  if (Number.isNaN(t.getTime()) || t.getTime() > now + 5 * 60_000 || t.getTime() < now - 24 * 3600_000) return new Date(now);
  return t;
}

export type SyncResult = { clientId: string; result: ScanResult | 'counter'; label: string | null; persons: number };

/**
 * Przyjmuje paczkę zdarzeń z telefonu (także zebranych offline) i zwraca ostateczny werdykt serwera.
 * Gdy dwa telefony offline wpuściły ten sam kod, drugi skan dostaje "duplicate" po synchronizacji.
 */
export async function applySync(eventId: string, input: SyncInput) {
  const results: SyncResult[] = [];
  for (const ev of input.events) {
    const r = await tx(async (c) => {
      const existing = await one<{ result: SyncResult['result']; label: string | null; persons: number }>(
        'select result, label, persons from door_events where event_id = $1 and client_id = $2', [eventId, ev.clientId], c,
      );
      if (existing) return { clientId: ev.clientId, ...existing };
      const at = clampTime(ev.at);
      if (ev.type !== 'scan') {
        const persons = ev.persons ?? 1;
        await q(
          `insert into door_events (event_id, device_id, client_id, type, persons, result, occurred_at) values ($1, $2, $3, $4, $5, 'counter', $6)
           on conflict (event_id, client_id) do nothing`,
          [eventId, input.deviceId, ev.clientId, ev.type, persons, at], c,
        );
        return { clientId: ev.clientId, result: 'counter' as const, label: null, persons };
      }
      const code = (ev.code ?? '').trim();
      const ref = code ? await resolveCode(c, eventId, code) : null;
      let result: ScanResult;
      if (!ref || ref.eventId !== eventId) result = 'invalid';
      else if (ref.void) result = 'void';
      else if (ref.used) result = 'duplicate';
      else if (ref.until && at > ref.until) result = ev.override ? 'override' : 'too_late';
      else result = 'ok';
      const label = ref && ref.eventId === eventId ? ref.label : ref ? 'Kod z innej imprezy' : null;
      const persons = ref?.persons ?? 1;
      if ((result === 'ok' || result === 'override') && ref) {
        await q(`update ${TABLE[ref.kind]} set checked_in_at = $2 where id = $1`, [ref.id, at], c);
      }
      await q(
        `insert into door_events (event_id, device_id, client_id, type, code, ref_kind, ref_id, persons, result, label, occurred_at)
         values ($1, $2, $3, 'scan', $4, $5, $6, $7, $8, $9, $10)`,
        [eventId, input.deviceId, ev.clientId, code.slice(0, 200), ref && ref.eventId === eventId ? ref.kind : null,
          ref && ref.eventId === eventId ? ref.id : null, persons, result, label, at],
        c,
      );
      return { clientId: ev.clientId, result, label, persons };
    });
    results.push(r);
  }
  // Kody wpuszczone w międzyczasie przez inne telefony — urządzenie oznaczy je u siebie jako użyte.
  const updates = await q<{ id: string; code: string }>(
    `select id, code from door_events where event_id = $1 and id > $2 and type = 'scan' and result in ('ok', 'override') order by id limit 5000`,
    [eventId, input.cursor],
  );
  const summary = await doorSummary(eventId);
  return { results, usedCodes: updates.map((u) => u.code), summary };
}

// ---------- Import biletów z innych platform ----------

const SOURCES = ['ra', 'going', 'biletomat', 'ebilet', 'other'] as const;
export type ExternalSource = (typeof SOURCES)[number];

/**
 * Wczytuje listę kodów z eksportu platformy (CSV lub kolumna kodów).
 * Format wiersza: kod[;imię i nazwisko[;rodzaj biletu]] — separator ; , albo tabulator.
 */
export async function importExternalTickets(eventId: string, source: string, text: string) {
  if (!SOURCES.includes(source as ExternalSource)) throw new UserError('Nieznane źródło biletów.');
  const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
  if (!lines.length) throw new UserError('Wklej kody biletów — jeden w wierszu.');
  if (lines.length > 20000) throw new UserError('Jednorazowo można wczytać do 20 000 kodów.');
  const sep = lines[0].includes('\t') ? '\t' : lines[0].includes(';') ? ';' : ',';
  const rows = lines
    .map((l) => l.split(sep).map((s) => s.trim().replace(/^"|"$/g, '')))
    .filter((cols, idx) => !(idx === 0 && /^(kod|code|barcode|ticket)/i.test(cols[0])))
    .filter((cols) => cols[0] && cols[0].length >= 4 && cols[0].length <= 200);
  let added = 0;
  await tx(async (c) => {
    for (const cols of rows) {
      const r = await c.query(
        `insert into external_tickets (event_id, source, code, holder_name, ticket_label) values ($1, $2, $3, $4, $5)
         on conflict (event_id, code) do nothing`,
        [eventId, source, cols[0], cols[1] || null, cols[2] || null],
      );
      added += r.rowCount ?? 0;
    }
  });
  return { added, skipped: rows.length - added };
}

export async function externalTicketCounts(eventId: string) {
  return q<{ source: string; total: number; entered: number }>(
    `select source, count(*)::int as total, count(checked_in_at)::int as entered from external_tickets where event_id = $1 group by source order by source`,
    [eventId],
  );
}
