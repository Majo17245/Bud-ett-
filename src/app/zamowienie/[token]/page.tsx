import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Qr } from '@/components/Qr';
import { orderByToken } from '@/lib/services/orders';
import { zl } from '@/lib/money';
import { fmtDate, fmtTime } from '@/lib/time';
import { t } from '@/lib/i18n';
import { AutoRefresh } from './AutoRefresh';

export const metadata = { title: 'Zamówienie', robots: { index: false } };

export default async function OrderPage({ params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  const o = await orderByToken(token);
  if (!o) notFound();
  const L = t[o.lang];
  return (
    <main className="narrow">
      <Link href={`/k/${o.org_slug}`} className="brand">{o.org_name}</Link>
      <h1 style={{ marginTop: 16 }}>{o.event_name}</h1>
      <p className="soft">{fmtDate(o.starts_at)} · {fmtTime(o.starts_at)} · {o.venue_name ?? o.org_name}{o.address ? `, ${o.address}` : ''}{o.min_age ? ` · ${o.min_age}+` : ''}</p>
      {o.status === 'pending' && (<><div className="flash info">{L.pending}</div><AutoRefresh /></>)}
      {o.status === 'paid' && <div className="flash ok">{L.paid}</div>}
      {o.status === 'cancelled' && <div className="flash bad">{L.cancelledOrder}</div>}

      {o.status === 'paid' && o.tickets.map((tk) => (
        <div key={tk.code} className={`qr-ticket ${tk.checked_in_at || tk.status === 'void' ? 'used' : ''}`}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>{tk.type_name}</div>
          <Qr value={tk.code} />
          <div className="code">{tk.code}</div>
          <div style={{ fontSize: '.85rem' }}>{o.buyer_name}{tk.checked_in_at ? ` · ${L.used}` : ''}</div>
        </div>
      ))}
      {o.status === 'paid' && o.lounge && (
        <div className={`qr-ticket ${o.lounge.status !== 'paid' ? 'used' : ''}`}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>{o.lounge.lounge_name} · {o.lounge.persons} os.</div>
          <Qr value={o.lounge.code} />
          <div className="code">{o.lounge.code}</div>
          <div style={{ fontSize: '.85rem' }}>{o.buyer_name}</div>
          <div style={{ fontSize: '.85rem' }}>{o.lang === 'en' ? 'Deposit paid' : 'Przedpłata'} {zl(o.lounge.prepay_amount)} / {zl(o.lounge.total_price)}</div>
        </div>
      )}
      <div className="card">
        <table>
          <tbody>
            <tr><td>{o.lang === 'en' ? 'Tickets / deposit' : 'Bilety / przedpłata'}</td><td className="num">{zl(o.subtotal)}</td></tr>
            {o.fee_payer === 'buyer' && o.service_fee > 0 && <tr><td>{L.fee}</td><td className="num">{zl(o.service_fee)}</td></tr>}
            <tr><td><strong>{L.total}</strong></td><td className="num"><strong>{zl(o.total)}</strong></td></tr>
          </tbody>
        </table>
        <p className="muted" style={{ fontSize: '.85rem', marginTop: 8 }}>
          {o.lang === 'en' ? 'Keep this link — it is your ticket. A copy was sent to' : 'Zachowaj ten link — to Twój bilet. Kopię wysłaliśmy na'} {o.buyer_email}.
        </p>
      </div>
    </main>
  );
}
