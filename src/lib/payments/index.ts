import { one } from '../db';
import { decryptSecret } from '../crypto';
import { env } from '../env';
import { p24Register, type P24Config } from './p24';

export type PaymentProvider = 'none' | 'mock' | 'przelewy24';

export async function p24ConfigForOrg(orgId: string): Promise<P24Config | null> {
  const o = await one<{ p24_merchant_id: number | null; p24_pos_id: number | null; p24_crc_enc: string | null; p24_api_key_enc: string | null; p24_sandbox: boolean }>(
    'select p24_merchant_id, p24_pos_id, p24_crc_enc, p24_api_key_enc, p24_sandbox from orgs where id = $1', [orgId],
  );
  if (!o?.p24_merchant_id || !o.p24_crc_enc || !o.p24_api_key_enc) return null;
  return {
    merchantId: o.p24_merchant_id,
    posId: o.p24_pos_id ?? o.p24_merchant_id,
    crc: decryptSecret(o.p24_crc_enc),
    apiKey: decryptSecret(o.p24_api_key_enc),
    sandbox: o.p24_sandbox,
  };
}

export function onlinePaymentsEnabled(provider: PaymentProvider) {
  if (provider === 'mock') return env.allowMockPayments;
  return provider === 'przelewy24';
}

/** Rozpoczyna płatność i zwraca adres, na który przekierowujemy kupującego. */
export async function startPayment(order: {
  id: string; org_id: string; public_token: string; total: number; buyer_email: string; buyer_name: string;
  lang: 'pl' | 'en'; payment_provider: PaymentProvider;
}, description: string): Promise<string> {
  if (order.payment_provider === 'mock') {
    if (!env.allowMockPayments) throw new Error('Płatności testowe są wyłączone (ALLOW_MOCK_PAYMENTS).');
    return `/platnosc-testowa/${order.public_token}`;
  }
  if (order.payment_provider === 'przelewy24') {
    const cfg = await p24ConfigForOrg(order.org_id);
    if (!cfg) throw new Error('Klub nie ma skonfigurowanych Przelewy24.');
    return p24Register(cfg, {
      sessionId: order.id,
      amount: order.total,
      description,
      email: order.buyer_email,
      client: order.buyer_name,
      language: order.lang,
      urlReturn: `${env.appUrl}/zamowienie/${order.public_token}`,
      urlStatus: `${env.appUrl}/api/platnosci/p24`,
    });
  }
  throw new Error('Płatności online nie są włączone w tym klubie.');
}
