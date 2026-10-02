import { sha384 } from '../crypto';

/**
 * Przelewy24 REST API v1. Płatność trafia na konto klubu u operatora (klub jest sprzedawcą),
 * więc nie przechowujemy cudzych pieniędzy — patrz "Biznesplan: prawo i regulacje".
 */
export type P24Config = { merchantId: number; posId: number; crc: string; apiKey: string; sandbox: boolean };

export function p24BaseUrl(sandbox: boolean) {
  return sandbox ? 'https://sandbox.przelewy24.pl' : 'https://secure.przelewy24.pl';
}

// Kolejność kluczy ma znaczenie — P24 liczy SHA-384 z JSON-a w tej kolejności.
export function registerSign(p: { sessionId: string; merchantId: number; amount: number; currency: string; crc: string }) {
  return sha384(JSON.stringify({ sessionId: p.sessionId, merchantId: p.merchantId, amount: p.amount, currency: p.currency, crc: p.crc }));
}

export type P24Notification = {
  merchantId: number; posId: number; sessionId: string; amount: number; originAmount: number;
  currency: string; orderId: number; methodId: number; statement: string; sign: string;
};

export function notificationSign(n: Omit<P24Notification, 'sign'>, crc: string) {
  return sha384(JSON.stringify({
    merchantId: n.merchantId, posId: n.posId, sessionId: n.sessionId, amount: n.amount, originAmount: n.originAmount,
    currency: n.currency, orderId: n.orderId, methodId: n.methodId, statement: n.statement, crc,
  }));
}

export function verifySign(p: { sessionId: string; orderId: number; amount: number; currency: string; crc: string }) {
  return sha384(JSON.stringify({ sessionId: p.sessionId, orderId: p.orderId, amount: p.amount, currency: p.currency, crc: p.crc }));
}

function authHeader(cfg: P24Config) {
  return 'Basic ' + Buffer.from(`${cfg.posId}:${cfg.apiKey}`).toString('base64');
}

export async function p24Register(cfg: P24Config, t: {
  sessionId: string; amount: number; description: string; email: string; client?: string;
  urlReturn: string; urlStatus: string; language: 'pl' | 'en';
}): Promise<string> {
  const body = {
    merchantId: cfg.merchantId,
    posId: cfg.posId,
    sessionId: t.sessionId,
    amount: t.amount,
    currency: 'PLN',
    description: t.description.slice(0, 1024),
    email: t.email,
    client: t.client,
    country: 'PL',
    language: t.language,
    urlReturn: t.urlReturn,
    urlStatus: t.urlStatus,
    timeLimit: 15,
    sign: registerSign({ sessionId: t.sessionId, merchantId: cfg.merchantId, amount: t.amount, currency: 'PLN', crc: cfg.crc }),
  };
  const res = await fetch(`${p24BaseUrl(cfg.sandbox)}/api/v1/transaction/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: authHeader(cfg) },
    body: JSON.stringify(body),
  });
  const json = (await res.json().catch(() => ({}))) as { data?: { token?: string }; error?: string };
  if (!res.ok || !json.data?.token) throw new Error(`Przelewy24 register: HTTP ${res.status} ${json.error ?? ''}`);
  return `${p24BaseUrl(cfg.sandbox)}/trnRequest/${json.data.token}`;
}

export async function p24Verify(cfg: P24Config, v: { sessionId: string; orderId: number; amount: number }): Promise<boolean> {
  const res = await fetch(`${p24BaseUrl(cfg.sandbox)}/api/v1/transaction/verify`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', Authorization: authHeader(cfg) },
    body: JSON.stringify({
      merchantId: cfg.merchantId,
      posId: cfg.posId,
      sessionId: v.sessionId,
      amount: v.amount,
      currency: 'PLN',
      orderId: v.orderId,
      sign: verifySign({ sessionId: v.sessionId, orderId: v.orderId, amount: v.amount, currency: 'PLN', crc: cfg.crc }),
    }),
  });
  const json = (await res.json().catch(() => ({}))) as { data?: { status?: string } };
  return res.ok && json.data?.status === 'success';
}
