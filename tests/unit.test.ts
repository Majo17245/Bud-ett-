import { describe, expect, it } from 'vitest';
import { applyDiscount, loungeFee, loungePrice, orderTotals, ticketFee } from '@/lib/pricing';
import { decryptSecret, encryptSecret, hashPassword, nameKey, newEntryCode, normalizePhone, sha384, verifyPassword } from '@/lib/crypto';
import { parseZl, zl } from '@/lib/money';
import { fromLocalInput, toLocalInput } from '@/lib/time';
import { notificationSign, registerSign } from '@/lib/payments/p24';
import { parseGuestLine } from '@/lib/services/lists';

describe('cennik', () => {
  it('opłata od biletu: 5% z minimum 1,49 zł w planie Start', () => {
    expect(ticketFee(3000, 'start')).toBe(150); // 5% z 30 zł = 1,50 zł
    expect(ticketFee(2000, 'start')).toBe(149); // 1,00 zł → minimum
    expect(ticketFee(10000, 'start')).toBe(500);
    expect(ticketFee(0, 'start')).toBe(0); // bilety bezpłatne bez opłaty
  });
  it('Premium: bilety 4%, loże 2%', () => {
    expect(ticketFee(10000, 'premium')).toBe(400);
    expect(loungeFee(100000, 'premium')).toBe(2000);
    expect(loungeFee(100000, 'klub')).toBe(2500);
  });
  it('kto płaci opłatę', () => {
    const lines = [{ quantity: 2, unitPrice: 3500, unitFee: 175 }];
    expect(orderTotals(lines, 'buyer')).toEqual({ subtotal: 7000, fee: 350, total: 7350, clubNet: 7000 });
    expect(orderTotals(lines, 'org')).toEqual({ subtotal: 7000, fee: 350, total: 7000, clubNet: 6650 });
  });
  it('rabat procentowy', () => {
    expect(applyDiscount(3500, 20)).toBe(2800);
    expect(applyDiscount(3500, null)).toBe(3500);
    expect(applyDiscount(3500, 100)).toBe(0);
  });
  it('cena loży z dopłatą za osoby i przedpłatą', () => {
    const l = { capacity: 5, max_capacity: 8, base_price: 100000, extra_person_price: 20000, prepay_percent: 80 };
    expect(loungePrice(l, 5)).toEqual({ total: 100000, prepay: 80000 });
    expect(loungePrice(l, 7)).toEqual({ total: 140000, prepay: 112000 });
    expect(() => loungePrice(l, 9)).toThrow();
  });
});

describe('kody i dane osobowe', () => {
  it('kody wejścia mają prefiks i 12 znaków bez mylących liter', () => {
    const c = newEntryCode('T');
    expect(c).toMatch(/^T[0-9A-HJKMNP-TV-Z]{11}$/);
    expect(new Set(Array.from({ length: 2000 }, () => newEntryCode('G'))).size).toBe(2000);
  });
  it('klucz nazwiska wykrywa duplikaty mimo kolejności i polskich znaków', () => {
    expect(nameKey('Łukasz Żółć')).toBe(nameKey('zolc  lukasz'));
    expect(nameKey('Jan Kowalski')).not.toBe(nameKey('Jan Kowalska'));
  });
  it('telefon w formacie E.164', () => {
    expect(normalizePhone('600 100 200')).toBe('+48600100200');
    expect(normalizePhone('+48 600-100-200')).toBe('+48600100200');
    expect(normalizePhone('12')).toBeNull();
  });
  it('hasła i szyfrowanie sekretów', async () => {
    const h = await hashPassword('bardzo-tajne-haslo');
    expect(await verifyPassword('bardzo-tajne-haslo', h)).toBe(true);
    expect(await verifyPassword('zle-haslo', h)).toBe(false);
    const enc = encryptSecret('crc-123');
    expect(enc).not.toContain('crc-123');
    expect(decryptSecret(enc)).toBe('crc-123');
  });
  it('wiersz listy "Jan Kowalski +2"', () => {
    expect(parseGuestLine('Jan Kowalski +2')).toEqual({ fullName: 'Jan Kowalski', plusOnes: 2 });
    expect(parseGuestLine('  Anna   Nowak ')).toEqual({ fullName: 'Anna Nowak', plusOnes: 0 });
    expect(parseGuestLine('   ')).toBeNull();
  });
});

describe('kwoty i czas', () => {
  it('formatowanie złotówek', () => {
    expect(zl(123450)).toBe('1 234,50 zł');
    expect(zl(3500)).toBe('35 zł');
    expect(parseZl('49,99')).toBe(4999);
    expect(parseZl('abc')).toBeNull();
  });
  it('czas lokalny Warszawy w obie strony (lato i zima)', () => {
    expect(fromLocalInput('2026-10-16T22:00')!.toISOString()).toBe('2026-10-16T20:00:00.000Z');
    expect(fromLocalInput('2026-12-31T22:00')!.toISOString()).toBe('2026-12-31T21:00:00.000Z');
    expect(toLocalInput(new Date('2026-10-16T20:00:00Z'))).toBe('2026-10-16T22:00');
  });
});

describe('Przelewy24', () => {
  it('podpis rejestracji liczony z JSON-a w kolejności z dokumentacji', () => {
    const expected = sha384('{"sessionId":"abc","merchantId":11111,"amount":100,"currency":"PLN","crc":"x"}');
    expect(registerSign({ sessionId: 'abc', merchantId: 11111, amount: 100, currency: 'PLN', crc: 'x' })).toBe(expected);
  });
  it('podpis powiadomienia', () => {
    const n = { merchantId: 1, posId: 1, sessionId: 's', amount: 100, originAmount: 100, currency: 'PLN', orderId: 5, methodId: 154, statement: 'p24-A1' };
    expect(notificationSign(n, 'crc')).toBe(sha384('{"merchantId":1,"posId":1,"sessionId":"s","amount":100,"originAmount":100,"currency":"PLN","orderId":5,"methodId":154,"statement":"p24-A1","crc":"crc"}'));
  });
});
