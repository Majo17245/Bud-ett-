import { notFound, redirect } from 'next/navigation';
import { env } from '@/lib/env';
import { one } from '@/lib/db';
import { cancelOrder, finalizeOrder } from '@/lib/services/orders';
import { zl } from '@/lib/money';

export const metadata = { title: 'Płatność testowa', robots: { index: false } };

async function pendingOrder(token: string) {
  if (!env.allowMockPayments) return null;
  return one<{ id: string; total: number; status: string; payment_provider: string; public_token: string }>(
    `select id, total, status, payment_provider, public_token from orders where public_token = $1 and payment_provider = 'mock'`, [token],
  );
}

async function payAction(fd: FormData) {
  'use server';
  const o = await pendingOrder(String(fd.get('token')));
  if (!o) notFound();
  if (fd.get('result') === 'ok') await finalizeOrder(o.id, `MOCK-${Date.now()}`);
  else await cancelOrder(o.id);
  redirect(`/zamowienie/${o.public_token}`);
}

/** Symulator operatora płatności — tylko gdy ALLOW_MOCK_PAYMENTS=true (dev, noc testowa). */
export default async function MockPaymentPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const o = await pendingOrder(token);
  if (!o) notFound();
  if (o.status !== 'pending') redirect(`/zamowienie/${o.public_token}`);
  return (
    <main className="narrow">
      <h1>Symulator płatności</h1>
      <div className="flash info">To środowisko testowe — żadne pieniądze nie zostaną pobrane. W produkcji w tym miejscu jest strona Przelewy24 z BLIK-iem i kartami.</div>
      <div className="card">
        <p>Do zapłaty: <strong>{zl(o.total)}</strong></p>
        <form action={payAction} className="row">
          <input type="hidden" name="token" value={o.public_token} />
          <button name="result" value="ok">Zapłać BLIK-iem (test)</button>
          <button name="result" value="cancel" className="ghost">Anuluj</button>
        </form>
      </div>
    </main>
  );
}
