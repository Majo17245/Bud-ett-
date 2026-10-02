import { one, q } from '../db';
import { doorSummary } from './door';
import { promoterStats } from './promoters';

/** Raport na żywo dla managera: sprzedaż, wejścia, kanały, listy, loże, promotorzy. */
export async function liveReport(orgId: string, eventId: string) {
  const [sales, byType, door, entriesByKind, timeline, lists, lounges, promoters, external] = await Promise.all([
    one<{ orders: number; tickets: number; gross: number; fees: number; online_lounges: number }>(
      `select count(*) filter (where o.kind = 'tickets')::int as orders,
         (select count(*) from tickets t where t.event_id = $1 and t.status = 'valid')::int as tickets,
         coalesce(sum(o.subtotal), 0)::int as gross,
         coalesce(sum(o.service_fee), 0)::int as fees,
         count(*) filter (where o.kind = 'lounge')::int as online_lounges
       from orders o where o.event_id = $1 and o.status = 'paid'`,
      [eventId],
    ),
    q<{ id: string; tier_group: string; name: string; price: number; quantity: number; sold: number; entered: number }>(
      `select tt.id, tt.tier_group, tt.name, tt.price, tt.quantity,
         (select count(*) from tickets t where t.ticket_type_id = tt.id and t.status = 'valid')::int as sold,
         (select count(*) from tickets t where t.ticket_type_id = tt.id and t.checked_in_at is not null)::int as entered
       from ticket_types tt where tt.event_id = $1 order by tt.sort_order`,
      [eventId],
    ),
    doorSummary(eventId),
    q<{ kind: string; persons: number }>(
      `select coalesce(ref_kind, 'licznik') as kind, sum(persons)::int as persons from door_events
       where event_id = $1 and ((type = 'scan' and result in ('ok', 'override')) or type = 'in') group by 1`,
      [eventId],
    ),
    q<{ slot: Date; persons: number; problems: number }>(
      `select date_bin('15 minutes', occurred_at, timestamptz '2000-01-01') as slot,
         coalesce(sum(persons) filter (where (type = 'scan' and result in ('ok', 'override')) or type = 'in'), 0)::int as persons,
         count(*) filter (where type = 'scan' and result not in ('ok', 'override'))::int as problems
       from door_events where event_id = $1 group by 1 order by 1`,
      [eventId],
    ),
    q<{ name: string; promoter_name: string | null; capacity: number; listed: number; entered: number }>(
      `select l.name, p.name as promoter_name, l.capacity,
         coalesce(sum(1 + g.plus_ones) filter (where g.status = 'invited'), 0)::int as listed,
         coalesce(sum(1 + g.plus_ones) filter (where g.status = 'invited' and g.checked_in_at is not null), 0)::int as entered
       from guest_lists l left join promoters p on p.id = l.promoter_id left join guest_entries g on g.list_id = l.id
       where l.event_id = $1 group by l.id, p.name order by l.created_at`,
      [eventId],
    ),
    one<{ booked: number; arrived: number; requested: number; no_show: number; value: number; prepaid: number }>(
      `select count(*) filter (where status in ('confirmed', 'paid'))::int as booked,
         count(*) filter (where status in ('confirmed', 'paid') and checked_in_at is not null)::int as arrived,
         count(*) filter (where status = 'requested')::int as requested,
         count(*) filter (where status = 'no_show')::int as no_show,
         coalesce(sum(total_price) filter (where status in ('confirmed', 'paid')), 0)::int as value,
         coalesce(sum(prepay_amount) filter (where status = 'paid'), 0)::int as prepaid
       from lounge_reservations where event_id = $1`,
      [eventId],
    ),
    promoterStats(orgId, eventId),
    q<{ source: string; total: number; entered: number }>(
      `select source, count(*)::int as total, count(checked_in_at)::int as entered from external_tickets where event_id = $1 group by source`,
      [eventId],
    ),
  ]);
  const problems = await q<{ result: string; n: number }>(
    `select result, count(*)::int as n from door_events where event_id = $1 and type = 'scan' and result not in ('ok', 'override') group by result`,
    [eventId],
  );
  return { sales: sales!, byType, door, entriesByKind, timeline, lists, lounges: lounges!, promoters, external, problems };
}

/** Krótkie podsumowanie nocy — wysyłane właścicielowi rano (raport poranny). */
export async function nightSummaryText(orgId: string, eventId: string, eventName: string) {
  const r = await liveReport(orgId, eventId);
  const zl = (g: number) => (g / 100).toLocaleString('pl-PL', { maximumFractionDigits: 0 }) + ' zł';
  const lines = [
    `${eventName}`,
    `Wejścia: ${r.door.entered} osób (bilety ${r.entriesByKind.find((k) => k.kind === 'ticket')?.persons ?? 0}, listy ${r.entriesByKind.find((k) => k.kind === 'guest')?.persons ?? 0}, loże ${r.entriesByKind.find((k) => k.kind === 'lounge')?.persons ?? 0}, inne platformy ${r.entriesByKind.find((k) => k.kind === 'external')?.persons ?? 0}).`,
    `Sprzedaż online: ${r.sales.tickets} biletów, ${zl(r.sales.gross)}.`,
    `Loże: ${r.lounges.booked} zarezerwowanych, ${r.lounges.arrived} przyszło, ${r.lounges.no_show} nie przyszło.`,
  ];
  const top = r.promoters.filter((p) => p.tickets + p.guests_entered > 0).slice(0, 3);
  if (top.length) lines.push('Promotorzy: ' + top.map((p) => `${p.name} ${p.tickets} bil. + ${p.guests_entered} z listy (prowizja ${zl(p.commission)})`).join('; ') + '.');
  const bad = r.problems.reduce((s, p) => s + p.n, 0);
  if (bad) lines.push(`Odrzucone skany: ${bad}.`);
  return lines.join('\n');
}
