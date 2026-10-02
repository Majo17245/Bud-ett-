import { afterAll, describe, expect, it } from 'vitest';
import { one, pool, q, UserError } from '@/lib/db';
import { addTicketType, ticketTypesWithState } from '@/lib/services/events';
import { createTicketOrder, createLoungeReservation, finalizeOrder, orderByToken, cancelOrder } from '@/lib/services/orders';
import { addGuests, createList } from '@/lib/services/lists';
import { addManualReservation, createLounge, setReservationStatus } from '@/lib/services/lounges';
import { applySync, buildManifest, createDoorToken, doorTokenValid, importExternalTickets } from '@/lib/services/door';
import { createPromoter, promoterByToken, promoterStats } from '@/lib/services/promoters';
import { createDiscountCode } from '@/lib/services/orgs';
import { liveReport } from '@/lib/services/reports';
import { buyer, fixture } from './helpers';

afterAll(() => pool().end());

const orderIdFromToken = async (token: string) => (await one<{ id: string }>('select id from orders where public_token = $1', [token]))!.id;
let seq = 0;
const scan = (code: string, extra: Partial<{ override: boolean; at: string }> = {}) => ({
  clientId: `test-${Date.now()}-${seq++}`, type: 'scan' as const, code, at: new Date().toISOString(), ...extra,
});

describe('sprzedaż biletów', () => {
  it('kupno z opłatą dla kupującego, płatność i wydanie biletów', async () => {
    const { event } = await fixture();
    const tt = await addTicketType(event.id, { name: 'I pula', price: 3500, quantity: 100 });
    const res = await createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: tt!.id, quantity: 2 }], buyer: buyer() });
    expect(res.redirectUrl).toBe(`/platnosc-testowa/${res.token}`);
    const pending = await orderByToken(res.token);
    expect(pending?.status).toBe('pending');
    expect(pending?.total).toBe(7000 + 2 * 175);
    expect(pending?.tickets).toHaveLength(0);

    const orderId = await orderIdFromToken(res.token);
    expect(await finalizeOrder(orderId, 'P24-1')).toBe(true);
    expect(await finalizeOrder(orderId, 'P24-1')).toBe(false); // powtórzone powiadomienie nic nie psuje
    const paid = await orderByToken(res.token);
    expect(paid?.status).toBe('paid');
    expect(paid?.tickets).toHaveLength(2);
  });

  it('pule cenowe: po wyprzedaniu early bird w sprzedaży jest kolejna pula', async () => {
    const { event } = await fixture();
    const early = await addTicketType(event.id, { name: 'Early bird', price: 2000, quantity: 2 });
    const first = await addTicketType(event.id, { name: 'I pula', price: 3000, quantity: 10 });
    let states = await ticketTypesWithState(event.id);
    expect(states.find((s) => s.id === early!.id)?.state).toBe('on_sale');
    expect(states.find((s) => s.id === first!.id)?.state).toBe('waiting');

    const r = await createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: early!.id, quantity: 2 }], buyer: buyer() });
    // Zamówienie w trakcie płatności blokuje bilety — early bird jest już niedostępny.
    states = await ticketTypesWithState(event.id);
    expect(states.find((s) => s.id === early!.id)?.state).toBe('sold_out');
    expect(states.find((s) => s.id === first!.id)?.state).toBe('on_sale');
    // Anulowanie zwalnia pulę.
    await cancelOrder(await orderIdFromToken(r.token));
    states = await ticketTypesWithState(event.id);
    expect(states.find((s) => s.id === early!.id)?.state).toBe('on_sale');
  });

  it('równoległe zamówienia nie sprzedadzą więcej niż jest w puli', async () => {
    const { event } = await fixture();
    const tt = await addTicketType(event.id, { name: 'Ostatnie', price: 3000, quantity: 5 });
    const attempts = await Promise.allSettled(
      Array.from({ length: 8 }, () => createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: tt!.id, quantity: 1 }], buyer: buyer() })),
    );
    expect(attempts.filter((a) => a.status === 'fulfilled')).toHaveLength(5);
    const rejected = attempts.filter((a): a is PromiseRejectedResult => a.status === 'rejected');
    expect(rejected).toHaveLength(3);
    for (const r of rejected) expect(r.reason).toBeInstanceOf(UserError);
  });

  it('bilety bezpłatne są wydawane od razu; płatne wymagają włączonych płatności', async () => {
    const { event } = await fixture({ provider: 'none' });
    const free = await addTicketType(event.id, { name: 'Wejście z zaproszeniem', price: 0, quantity: 50 });
    const paidType = await addTicketType(event.id, { tierGroup: 'Płatne', name: 'Bilet', price: 3000, quantity: 50 });
    const r = await createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: free!.id, quantity: 3 }], buyer: buyer() });
    expect(r.redirectUrl).toBe(`/zamowienie/${r.token}`);
    expect((await orderByToken(r.token))?.tickets).toHaveLength(3);
    await expect(createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: paidType!.id, quantity: 1 }], buyer: buyer() }))
      .rejects.toThrow(/nie sprzedaje jeszcze biletów online/);
  });

  it('bilet grupowy wydaje kod dla każdej osoby; kod rabatowy obniża cenę', async () => {
    const { org, event } = await fixture({ feePayer: 'org' });
    const group = await addTicketType(event.id, { name: 'Paczka 4 osoby', price: 12000, quantity: 10, groupSize: 4 });
    await createDiscountCode(org.id, event.id, { code: 'STUDENT', percentOff: 25, maxUses: 1 });
    const r = await createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: group!.id, quantity: 1 }], buyer: buyer(), discountCode: 'student' });
    const o = await orderByToken(r.token);
    expect(o?.total).toBe(9000); // klub płaci opłatę, kupujący płaci cenę po rabacie
    await finalizeOrder(await orderIdFromToken(r.token), null);
    expect((await orderByToken(r.token))?.tickets).toHaveLength(4);
    await expect(createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: group!.id, quantity: 1 }], buyer: buyer(), discountCode: 'STUDENT' }))
      .rejects.toThrow(/wyczerpał/);
  });

  it('wymaga regulaminu i poprawnego e-maila', async () => {
    const { event } = await fixture();
    const tt = await addTicketType(event.id, { name: 'I pula', price: 3000, quantity: 10 });
    await expect(createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: tt!.id, quantity: 1 }], buyer: { ...buyer(), termsAccepted: false } })).rejects.toThrow(/regulamin/);
    await expect(createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: tt!.id, quantity: 1 }], buyer: { ...buyer(), email: 'zly' } })).rejects.toThrow(/e-mail/);
  });
});

describe('listy gości', () => {
  it('limit listy i blokada duplikatów między listami', async () => {
    const { event } = await fixture();
    const a = await createList(event.id, { name: 'Lista A', capacity: 3 });
    const b = await createList(event.id, { name: 'Lista B', capacity: 10 });
    await addGuests(a!.id, [{ fullName: 'Jan Kowalski', plusOnes: 1 }], 'test');
    await expect(addGuests(a!.id, [{ fullName: 'Anna Nowak', plusOnes: 1 }], 'test')).rejects.toThrow(/Limit listy to 3/);
    await expect(addGuests(b!.id, [{ fullName: 'kowalski jan' }], 'test')).rejects.toThrow(/jest już na liście „Lista A”/);
    const ok = await addGuests(b!.id, [{ fullName: 'Anna Nowak' }, { fullName: 'Piotr Zieliński', plusOnes: 2 }], 'test');
    expect(ok).toHaveLength(2);
  });
});

describe('loże', () => {
  it('przedpłata online i blokada podwójnej rezerwacji', async () => {
    const { org, event } = await fixture({ plan: 'klub' });
    const l = await createLounge(org.id, { name: 'Loża 1', capacity: 5, maxCapacity: 8, basePrice: 100000, extraPersonPrice: 20000, prepayPercent: 50 });
    const r = await createLoungeReservation({ eventId: event.id, loungeId: l!.id, persons: 6, buyer: buyer() });
    expect(r.mode).toBe('prepay');
    const token = r.redirectUrl.split('/').pop()!;
    const o = await orderByToken(token);
    expect(o?.subtotal).toBe(60000); // 50% z 1 200 zł
    expect(o?.service_fee).toBe(1500); // 2,5%
    await expect(createLoungeReservation({ eventId: event.id, loungeId: l!.id, persons: 4, buyer: buyer() })).rejects.toThrow(/zarezerwowana/);
    await finalizeOrder(await orderIdFromToken(token), null);
    expect((await orderByToken(token))?.lounge?.status).toBe('paid');
  });

  it('bez płatności online: prośba, którą manager potwierdza', async () => {
    const { org, event } = await fixture({ provider: 'none' });
    const l = await createLounge(org.id, { name: 'Loża 2', capacity: 4, maxCapacity: 6, basePrice: 50000 });
    const r1 = await createLoungeReservation({ eventId: event.id, loungeId: l!.id, persons: 4, buyer: buyer() });
    const r2 = await createLoungeReservation({ eventId: event.id, loungeId: l!.id, persons: 4, buyer: buyer() });
    expect(r1.mode).toBe('request');
    const reqs = await q<{ id: string }>(`select id from lounge_reservations where event_id = $1 order by created_at`, [event.id]);
    await setReservationStatus(event.id, reqs[0].id, 'confirmed');
    await expect(setReservationStatus(event.id, reqs[1].id, 'confirmed')).rejects.toThrow(/zarezerwowana/);
    await expect(addManualReservation(org.id, event.id, { loungeId: l!.id, name: 'Telefon', persons: 3, source: 'phone' })).rejects.toThrow(/zarezerwowana/);
    expect(r2.mode).toBe('request');
  });
});

describe('bramka', () => {
  it('skan, duplikat, lista po godzinie, nieznany kod, licznik osób i synchronizacja telefonów', async () => {
    const { org, event } = await fixture({ provider: 'none' });
    const free = await addTicketType(event.id, { name: 'Wejściówka', price: 0, quantity: 10 });
    const order = await createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: free!.id, quantity: 1 }], buyer: buyer() });
    const ticketCode = (await orderByToken(order.token))!.tickets[0].code;
    const early = await createList(event.id, { name: 'Do 23', capacity: 10, entryUntil: new Date(Date.now() - 60_000) });
    const [late] = await addGuests(early!.id, [{ fullName: 'Spóźniony Gość', plusOnes: 1 }], 'test');
    const l = await createLounge(org.id, { name: 'VIP', capacity: 6, maxCapacity: 8, basePrice: 100000 });
    const lounge = await addManualReservation(org.id, event.id, { loungeId: l!.id, name: 'Pan VIP', persons: 6, source: 'dm' });
    await importExternalTickets(event.id, 'ra', 'code;name\nRA-12345;Ewa RA\nRA-99999;Olek RA');

    const manifest = await buildManifest(event.id);
    expect(manifest!.entries.map((e) => e.c).sort()).toEqual([ticketCode, late.code, lounge!.code, 'RA-12345', 'RA-99999'].sort());

    const phoneA = await applySync(event.id, {
      deviceId: 'telefon-A', cursor: 0,
      events: [scan(ticketCode), scan(ticketCode), scan(late.code), scan('NIEZNANY-KOD'), scan(lounge!.code), scan('RA-12345')],
    });
    expect(phoneA.results.map((r) => r.result)).toEqual(['ok', 'duplicate', 'too_late', 'invalid', 'ok', 'ok']);

    // Manager decyduje się wpuścić gościa po czasie; telefon B był offline i wpuścił ten sam bilet.
    const phoneB = await applySync(event.id, {
      deviceId: 'telefon-B', cursor: 0,
      events: [scan(late.code, { override: true }), scan(ticketCode), { clientId: 'out-1-' + seq++, type: 'out', persons: 2, at: new Date().toISOString() }],
    });
    expect(phoneB.results.map((r) => r.result)).toEqual(['override', 'duplicate', 'counter']);
    expect(phoneB.usedCodes).toContain(ticketCode);
    // 1 bilet + 6 loża + 1 RA + 2 z listy po czasie − 2 wyszło
    expect(phoneB.summary.inside).toBe(8);
    expect(phoneB.summary.entered).toBe(10);

    // Ponowne wysłanie tej samej paczki (np. po utracie zasięgu) nic nie zmienia.
    const again = await applySync(event.id, { deviceId: 'telefon-A', cursor: 0, events: [] });
    expect(again.summary.inside).toBe(8);

    const report = await liveReport(org.id, event.id);
    expect(report.door.entered).toBe(10);
    expect(report.lounges.arrived).toBe(1);
    expect(report.problems.find((p) => p.result === 'duplicate')?.n).toBe(2);
  });

  it('tokeny bramki działają tylko dla swojej imprezy', async () => {
    const a = await fixture();
    const b = await fixture();
    const token = await createDoorToken(a.event.id, 'Wejście 1');
    expect(await doorTokenValid(a.event.id, token)).toBe(true);
    expect(await doorTokenValid(b.event.id, token)).toBe(false);
    expect(await doorTokenValid(a.event.id, 'zly-token')).toBe(false);
  });
});

describe('promotorzy', () => {
  it('sprzedaż z linku promotora, lista promotora i prowizja', async () => {
    const { org, event } = await fixture();
    const p = await createPromoter(org.id, { name: 'Kamil', ticketCommissionPct: 10, guestCommission: 500 });
    expect(p.code).toBe('KAMIL');
    expect((await promoterByToken(p.panelToken))?.id).toBe(p.id);
    const tt = await addTicketType(event.id, { name: 'I pula', price: 4000, quantity: 50 });
    const r = await createTicketOrder({ eventId: event.id, items: [{ ticketTypeId: tt!.id, quantity: 3 }], buyer: buyer(), promoterCode: 'kamil' });
    await finalizeOrder(await orderIdFromToken(r.token), null);
    const list = await createList(event.id, { name: 'Lista Kamila', capacity: 20, promoterId: p.id });
    const [g] = await addGuests(list!.id, [{ fullName: 'Ola Lis', plusOnes: 1 }], 'promoter', { promoterId: p.id });
    await applySync(event.id, { deviceId: 'tel', cursor: 0, events: [scan(g.code)] });
    const [stats] = await promoterStats(org.id, event.id);
    expect(stats).toMatchObject({ tickets: 3, ticket_revenue: 12000, guests_listed: 2, guests_entered: 2 });
    expect(stats.commission).toBe(1200 + 2 * 500);
  });
});
