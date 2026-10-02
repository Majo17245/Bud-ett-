import { one } from '@/lib/db';
import { p24ConfigForOrg } from '@/lib/payments';
import { notificationSign, p24Verify, type P24Notification } from '@/lib/payments/p24';
import { finalizeOrder } from '@/lib/services/orders';

/**
 * Powiadomienie Przelewy24 (urlStatus). Sprawdzamy podpis i kwotę, potwierdzamy transakcję
 * w P24 (verify) i dopiero wtedy wydajemy bilety. Odpowiedź 200 kończy ponawianie po stronie P24.
 */
export async function POST(req: Request) {
  const n = (await req.json().catch(() => null)) as P24Notification | null;
  if (!n?.sessionId || !/^[0-9a-f-]{36}$/i.test(n.sessionId)) return new Response('bad request', { status: 400 });
  const order = await one<{ id: string; org_id: string; total: number; status: string }>(
    `select id, org_id, total, status from orders where id = $1 and payment_provider = 'przelewy24'`, [n.sessionId],
  );
  if (!order) return new Response('unknown order', { status: 404 });
  if (order.status === 'paid') return new Response('OK');
  const cfg = await p24ConfigForOrg(order.org_id);
  if (!cfg) return new Response('not configured', { status: 409 });
  const { sign, ...rest } = n;
  if (notificationSign(rest, cfg.crc) !== sign || n.merchantId !== cfg.merchantId) {
    console.warn('[p24] zły podpis powiadomienia', n.sessionId);
    return new Response('bad sign', { status: 400 });
  }
  if (n.amount !== order.total || n.currency !== 'PLN') {
    console.error('[p24] kwota niezgodna z zamówieniem', n.sessionId, n.amount, order.total);
    return new Response('amount mismatch', { status: 400 });
  }
  const ok = await p24Verify(cfg, { sessionId: n.sessionId, orderId: n.orderId, amount: n.amount });
  if (!ok) return new Response('verify failed', { status: 502 });
  await finalizeOrder(order.id, String(n.orderId));
  return new Response('OK');
}
