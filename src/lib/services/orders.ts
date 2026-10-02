import type { PoolClient } from 'pg';
import { one, q, tx, UserError } from '../db';
import { newEntryCode, normalizePhone, randomToken } from '../crypto';
import { env } from '../env';
import { sendMail } from '../mailer';
import { zl } from '../money';
import { applyDiscount, loungeFee, loungePrice, orderTotals, ticketFee, type FeePayer, type Plan } from '../pricing';
import { onlinePaymentsEnabled, startPayment, type PaymentProvider } from '../payments';
import { fmtDateTime } from '../time';
import { ticketTypesWithState } from './events';
import { upsertGuest } from './guests';

export const ORDER_HOLD_MINUTES = 15;
export const MAX_TICKETS_PER_ORDER = 10;

export type BuyerInput = {
  name: string; email: string; phone?: string | null; lang?: 'pl' | 'en';
  marketingConsent?: boolean; termsAccepted: boolean;
};

type EventForSale = {
  id: string; org_id: string; name: string; slug: string; starts_at: Date; org_slug: string; org_name: string;
  plan: Plan; fee_payer: FeePayer; payment_provider: PaymentProvider; contact_email: string | null;
};

function validateBuyer(b: BuyerInput) {
  if (!b.name?.trim() || b.name.trim().length < 3) throw new UserError('Podaj imię i nazwisko.');
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(b.email?.trim() ?? '')) throw new UserError('Podaj poprawny adres e-mail — wyślemy na niego bilety.');
  if (!b.termsAccepted) throw new UserError('Zaakceptuj regulamin, aby kupić bilet.');
}

async function eventForSale(c: PoolClient, eventId: string): Promise<EventForSale> {
  const e = await one<EventForSale>(
    `select e.id, e.org_id, e.name, e.slug, e.starts_at, o.slug as org_slug, o.name as org_name,
            o.plan, o.fee_payer, o.payment_provider, o.contact_email
     from events e join orgs o on o.id = e.org_id
     where e.id = $1 and e.status = 'published' and e.ends_at > now()`,
    [eventId], c,
  );
  if (!e) throw new UserError('Sprzedaż na tę imprezę jest zamknięta.');
  return e;
}

async function promoterIdByCode(c: PoolClient, orgId: string, code?: string | null) {
  if (!code) return null;
  const p = await one<{ id: string }>(
    'select id from promoters where org_id = $1 and code = $2 and active', [orgId, code.trim().toUpperCase()], c,
  );
  return p?.id ?? null;
}

async function insertOrder(c: PoolClient, o: {
  e: EventForSale; kind: 'tickets' | 'lounge'; buyer: BuyerInput; totals: ReturnType<typeof orderTotals>;
  promoterId: string | null; discountCodeId: string | null;
}) {
  const provider: PaymentProvider = o.totals.total > 0 ? o.e.payment_provider : 'none';
  return (await one<{ id: string; public_token: string }>(
    `insert into orders (org_id, event_id, public_token, kind, buyer_name, buyer_email, buyer_phone, lang,
       subtotal, service_fee, total, fee_payer, promoter_id, discount_code_id, marketing_consent, payment_provider, expires_at)
     values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, now() + make_interval(mins => $17))
     returning id, public_token`,
    [o.e.org_id, o.e.id, randomToken(18), o.kind, o.buyer.name.trim(), o.buyer.email.trim().toLowerCase(),
      normalizePhone(o.buyer.phone), o.buyer.lang ?? 'pl', o.totals.subtotal, o.totals.fee, o.totals.total, o.e.fee_payer,
      o.promoterId, o.discountCodeId, !!o.buyer.marketingConsent, provider, ORDER_HOLD_MINUTES],
    c,
  ))!;
}

/** Zakup biletów. Zwraca adres, na który należy przekierować kupującego. */
export async function createTicketOrder(input: {
  eventId: string;
  items: { ticketTypeId: string; quantity: number }[];
  buyer: BuyerInput;
  discountCode?: string | null;
  promoterCode?: string | null;
}): Promise<{ token: string; redirectUrl: string }> {
  validateBuyer(input.buyer);
  const items = input.items.filter((i) => Number.isInteger(i.quantity) && i.quantity > 0);
  if (!items.length) throw new UserError('Wybierz co najmniej jeden bilet.');
  const totalQty = items.reduce((s, i) => s + i.quantity, 0);
  if (totalQty > MAX_TICKETS_PER_ORDER) throw new UserError(`Jednorazowo możesz kupić maksymalnie ${MAX_TICKETS_PER_ORDER} biletów.`);

  const created = await tx(async (c) => {
    const e = await eventForSale(c, input.eventId);
    // Blokada wierszy pul — równoległe zamówienia nie sprzedadzą więcej, niż jest w puli.
    const types = await ticketTypesWithState(e.id, c, { forUpdate: true });

    let percentOff: number | null = null;
    let discountCodeId: string | null = null;
    if (input.discountCode?.trim()) {
      const d = await one<{ id: string; percent_off: number; max_uses: number | null; used: number }>(
        `select id, percent_off, max_uses, used from discount_codes
         where org_id = $1 and code = $2 and active and (event_id is null or event_id = $3) for update`,
        [e.org_id, input.discountCode.trim().toUpperCase(), e.id], c,
      );
      if (!d || (d.max_uses != null && d.used >= d.max_uses)) throw new UserError('Kod rabatowy jest nieprawidłowy albo już się wyczerpał.');
      percentOff = d.percent_off;
      discountCodeId = d.id;
    }

    const lines = items.map((it) => {
      const t = types.find((x) => x.id === it.ticketTypeId);
      if (!t || t.state !== 'on_sale') throw new UserError('Wybrana pula biletów nie jest już w sprzedaży — odśwież stronę.');
      if (it.quantity > t.remaining) throw new UserError(`W puli „${t.name}” zostało tylko ${t.remaining} szt.`);
      const unitPrice = applyDiscount(t.price, percentOff);
      return { ticketTypeId: t.id, quantity: it.quantity, unitPrice, unitFee: ticketFee(unitPrice, e.plan) };
    });
    const totals = orderTotals(lines, e.fee_payer);
    if (totals.total > 0 && !onlinePaymentsEnabled(e.payment_provider)) {
      throw new UserError('Ten klub nie sprzedaje jeszcze biletów online — kupisz je na miejscu.');
    }

    const order = await insertOrder(c, {
      e, kind: 'tickets', buyer: input.buyer, totals,
      promoterId: await promoterIdByCode(c, e.org_id, input.promoterCode), discountCodeId,
    });
    for (const l of lines) {
      await q(
        'insert into order_items (order_id, ticket_type_id, quantity, unit_price, unit_fee) values ($1, $2, $3, $4, $5)',
        [order.id, l.ticketTypeId, l.quantity, l.unitPrice, l.unitFee], c,
      );
    }
    if (totals.total === 0) await finalizeInTx(c, order.id, null);
    return { order, e, totals };
  });

  const { order, e, totals } = created;
  if (totals.total === 0) {
    await sendOrderConfirmation(order.id);
    return { token: order.public_token, redirectUrl: `/zamowienie/${order.public_token}` };
  }
  try {
    const redirectUrl = await startPayment(
      { id: order.id, org_id: e.org_id, public_token: order.public_token, total: totals.total, buyer_email: input.buyer.email.trim(),
        buyer_name: input.buyer.name.trim(), lang: input.buyer.lang ?? 'pl', payment_provider: e.payment_provider },
      `Bilety: ${e.name} (${e.org_name})`,
    );
    return { token: order.public_token, redirectUrl };
  } catch (err) {
    console.error('[płatność] nie udało się rozpocząć', err);
    await q(`update orders set status = 'cancelled' where id = $1 and status = 'pending'`, [order.id]);
    throw new UserError('Nie udało się rozpocząć płatności. Spróbuj ponownie za chwilę.');
  }
}

/** Rezerwacja loży: z przedpłatą online (gdy klub ma płatności) albo jako prośba do managera. */
export async function createLoungeReservation(input: {
  eventId: string; loungeId: string; persons: number; buyer: BuyerInput; promoterCode?: string | null; notes?: string | null;
}): Promise<{ redirectUrl: string; mode: 'prepay' | 'request' }> {
  validateBuyer(input.buyer);
  const created = await tx(async (c) => {
    const e = await eventForSale(c, input.eventId);
    const lounge = await one<{ id: string; name: string; capacity: number; max_capacity: number; base_price: number; extra_person_price: number; prepay_percent: number }>(
      'select * from lounges where id = $1 and org_id = $2 and active for update', [input.loungeId, e.org_id], c,
    );
    if (!lounge) throw new UserError('Nie ma takiej loży.');
    await assertLoungeFree(c, e.id, lounge.id);
    let price;
    try {
      price = loungePrice(lounge, input.persons);
    } catch (err) {
      throw new UserError((err as Error).message);
    }
    const promoterId = await promoterIdByCode(c, e.org_id, input.promoterCode);
    const prepayOnline = price.prepay > 0 && onlinePaymentsEnabled(e.payment_provider);
    const res = (await one<{ id: string; code: string }>(
      `insert into lounge_reservations (event_id, lounge_id, status, name, phone, email, persons, total_price, prepay_amount,
         promoter_id, source, notes, code, hold_until)
       values ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'web', $11, $12,
         case when $3 = 'pending_payment' then now() + make_interval(mins => $13) end)
       returning id, code`,
      [e.id, lounge.id, prepayOnline ? 'pending_payment' : 'requested', input.buyer.name.trim(), normalizePhone(input.buyer.phone),
        input.buyer.email.trim().toLowerCase(), input.persons, price.total, price.prepay, promoterId,
        input.notes?.trim().slice(0, 500) || null, newEntryCode('L'), ORDER_HOLD_MINUTES],
      c,
    ))!;
    if (!prepayOnline) {
      await upsertGuest(c, e.org_id, { email: input.buyer.email, phone: normalizePhone(input.buyer.phone), name: input.buyer.name, consent: input.buyer.marketingConsent, source: 'loża' });
      return { e, lounge, price, reservation: res, order: null as null | { id: string; public_token: string }, totals: null as null | ReturnType<typeof orderTotals> };
    }
    const unitFee = loungeFee(price.prepay, e.plan);
    const totals = orderTotals([{ quantity: 1, unitPrice: price.prepay, unitFee }], e.fee_payer);
    const order = await insertOrder(c, { e, kind: 'lounge', buyer: input.buyer, totals, promoterId, discountCodeId: null });
    await q(
      'insert into order_items (order_id, lounge_reservation_id, quantity, unit_price, unit_fee) values ($1, $2, 1, $3, $4)',
      [order.id, res.id, price.prepay, unitFee], c,
    );
    await q('update lounge_reservations set order_id = $2 where id = $1', [res.id, order.id], c);
    return { e, lounge, price, reservation: res, order, totals };
  });

  const { e, lounge, price, order, totals } = created;
  if (!order || !totals) {
    if (e.contact_email) {
      await sendMail({
        to: e.contact_email,
        subject: `Nowa prośba o lożę: ${lounge.name}, ${e.name}`,
        text: `${input.buyer.name} (${input.buyer.phone ?? 'bez telefonu'}, ${input.buyer.email}) prosi o lożę ${lounge.name} dla ${input.persons} osób na ${e.name} (${fmtDateTime(e.starts_at)}).\nCena: ${zl(price.total)}.\nPotwierdź w panelu: ${env.appUrl}/panel/${e.org_slug}/wydarzenia/${e.id}/loze`,
      });
    }
    return { mode: 'request', redirectUrl: `/k/${e.org_slug}/e/${e.slug}?loza=wyslana` };
  }
  try {
    const redirectUrl = await startPayment(
      { id: order.id, org_id: e.org_id, public_token: order.public_token, total: totals.total, buyer_email: input.buyer.email.trim(),
        buyer_name: input.buyer.name.trim(), lang: input.buyer.lang ?? 'pl', payment_provider: e.payment_provider },
      `Przedpłata za lożę ${lounge.name}: ${e.name}`,
    );
    return { mode: 'prepay', redirectUrl };
  } catch (err) {
    console.error('[płatność] nie udało się rozpocząć', err);
    await cancelOrder(order.id);
    throw new UserError('Nie udało się rozpocząć płatności. Spróbuj ponownie za chwilę.');
  }
}

export async function assertLoungeFree(c: PoolClient, eventId: string, loungeId: string, exceptReservationId?: string) {
  const taken = await one(
    `select 1 from lounge_reservations where event_id = $1 and lounge_id = $2 and id <> coalesce($3::uuid, '00000000-0000-0000-0000-000000000000')
       and (status in ('confirmed', 'paid') or (status = 'pending_payment' and hold_until > now()))`,
    [eventId, loungeId, exceptReservationId ?? null], c,
  );
  if (taken) throw new UserError('Ta loża jest już zarezerwowana na tę noc.');
}

/** Oznacza zamówienie jako opłacone i wydaje bilety. Idempotentne — bezpieczne przy powtórzonych powiadomieniach. */
export async function finalizeOrder(orderId: string, providerOrderId: string | null): Promise<boolean> {
  const newlyPaid = await tx((c) => finalizeInTx(c, orderId, providerOrderId));
  if (newlyPaid) await sendOrderConfirmation(orderId);
  return newlyPaid;
}

async function finalizeInTx(c: PoolClient, orderId: string, providerOrderId: string | null): Promise<boolean> {
  const order = await one<{ id: string; org_id: string; event_id: string; status: string; total: number; buyer_email: string; buyer_phone: string | null; buyer_name: string; marketing_consent: boolean; discount_code_id: string | null }>(
    'select * from orders where id = $1 for update', [orderId], c,
  );
  if (!order) throw new Error(`Brak zamówienia ${orderId}`);
  if (order.status === 'paid' || order.status === 'refunded') return false;
  if (order.status === 'cancelled') {
    // Pieniądze wpłynęły mimo anulowania (np. płatność po czasie) — wydajemy bilety, klub może zwrócić środki.
    console.warn(`[płatność] opłacono anulowane zamówienie ${orderId}`);
  }
  await q(`update orders set status = 'paid', paid_at = now(), provider_order_id = $2 where id = $1`, [orderId, providerOrderId], c);

  const items = await q<{ ticket_type_id: string | null; lounge_reservation_id: string | null; quantity: number; group_size: number | null }>(
    `select oi.ticket_type_id, oi.lounge_reservation_id, oi.quantity, tt.group_size
     from order_items oi left join ticket_types tt on tt.id = oi.ticket_type_id where oi.order_id = $1`,
    [orderId], c,
  );
  for (const it of items) {
    if (it.ticket_type_id) {
      const count = it.quantity * (it.group_size ?? 1);
      for (let i = 0; i < count; i++) {
        await q('insert into tickets (order_id, event_id, ticket_type_id, code) values ($1, $2, $3, $4)',
          [orderId, order.event_id, it.ticket_type_id, newEntryCode('T')], c);
      }
    }
    if (it.lounge_reservation_id) {
      const r = await one<{ lounge_id: string }>('select lounge_id from lounge_reservations where id = $1 for update', [it.lounge_reservation_id], c);
      const conflict = await one(
        `select 1 from lounge_reservations where event_id = $1 and lounge_id = $2 and id <> $3 and status in ('confirmed', 'paid')`,
        [order.event_id, r!.lounge_id, it.lounge_reservation_id], c,
      );
      if (conflict) {
        await q(`update lounge_reservations set status = 'cancelled', notes = coalesce(notes || ' | ', '') || 'Przedpłata po czasie, loża zajęta — zwrot środków.' where id = $1`, [it.lounge_reservation_id], c);
        console.warn(`[loża] przedpłata po czasie dla rezerwacji ${it.lounge_reservation_id} — wymaga zwrotu`);
      } else {
        await q(`update lounge_reservations set status = 'paid', hold_until = null where id = $1`, [it.lounge_reservation_id], c);
      }
    }
  }
  if (order.discount_code_id) await q('update discount_codes set used = used + 1 where id = $1', [order.discount_code_id], c);
  await upsertGuest(c, order.org_id, {
    email: order.buyer_email, phone: order.buyer_phone, name: order.buyer_name, consent: order.marketing_consent,
    source: 'zakup', spent: order.total, order: true,
  });
  return true;
}

export async function cancelOrder(orderId: string) {
  await tx(async (c) => {
    const o = await one<{ status: string }>('select status from orders where id = $1 for update', [orderId], c);
    if (o?.status !== 'pending') return;
    await q(`update orders set status = 'cancelled' where id = $1`, [orderId], c);
    await q(`update lounge_reservations set status = 'cancelled' where order_id = $1 and status = 'pending_payment'`, [orderId], c);
  });
}

export async function orderByToken(token: string) {
  if (!/^[A-Za-z0-9_-]{10,64}$/.test(token)) return null;
  const order = await one<{
    id: string; status: string; kind: string; buyer_name: string; buyer_email: string; total: number; subtotal: number; service_fee: number;
    fee_payer: string; payment_provider: string; created_at: Date; lang: 'pl' | 'en'; public_token: string;
    event_id: string; event_name: string; event_slug: string; starts_at: Date; ends_at: Date; venue_name: string | null; min_age: number | null;
    org_name: string; org_slug: string; address: string | null;
  }>(
    `select o.id, o.status, o.kind, o.buyer_name, o.buyer_email, o.total, o.subtotal, o.service_fee, o.fee_payer, o.payment_provider,
            o.created_at, o.lang, o.public_token, e.id as event_id, e.name as event_name, e.slug as event_slug, e.starts_at, e.ends_at, e.venue_name, e.min_age,
            g.name as org_name, g.slug as org_slug, g.address
     from orders o join events e on e.id = o.event_id join orgs g on g.id = o.org_id where o.public_token = $1`,
    [token],
  );
  if (!order) return null;
  const tickets = await q<{ code: string; type_name: string; status: string; checked_in_at: Date | null }>(
    `select t.code, tt.name as type_name, t.status, t.checked_in_at from tickets t join ticket_types tt on tt.id = t.ticket_type_id
     where t.order_id = $1 order by tt.sort_order, t.created_at`,
    [order.id],
  );
  const lounge = await one<{ code: string; status: string; persons: number; total_price: number; prepay_amount: number; lounge_name: string }>(
    `select r.code, r.status, r.persons, r.total_price, r.prepay_amount, l.name as lounge_name
     from lounge_reservations r join lounges l on l.id = r.lounge_id where r.order_id = $1`,
    [order.id],
  );
  return { ...order, tickets, lounge };
}

async function sendOrderConfirmation(orderId: string) {
  const o = await one<{ public_token: string; buyer_email: string; lang: string; kind: string; event_name: string; starts_at: Date; org_name: string; total: number }>(
    `select o.public_token, o.buyer_email, o.lang, o.kind, e.name as event_name, e.starts_at, g.name as org_name, o.total
     from orders o join events e on e.id = o.event_id join orgs g on g.id = o.org_id where o.id = $1`,
    [orderId],
  );
  if (!o) return;
  const link = `${env.appUrl}/zamowienie/${o.public_token}`;
  const en = o.lang === 'en';
  const what = o.kind === 'lounge' ? (en ? 'Your table reservation' : 'Twoja rezerwacja loży') : (en ? 'Your tickets' : 'Twoje bilety');
  await sendMail({
    to: o.buyer_email,
    subject: `${what}: ${o.event_name}`,
    text: en
      ? `${what} for ${o.event_name} (${o.org_name}, ${fmtDateTime(o.starts_at)}).\nShow the QR code at the door: ${link}\nPaid: ${zl(o.total)}`
      : `${what} na ${o.event_name} (${o.org_name}, ${fmtDateTime(o.starts_at)}).\nKod QR do pokazania na bramce: ${link}\nZapłacono: ${zl(o.total)}`,
  });
}
