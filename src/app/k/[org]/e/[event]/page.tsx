import Link from 'next/link';
import { notFound } from 'next/navigation';
import { cookies, headers } from 'next/headers';
import type { Metadata } from 'next';
import { Flash } from '@/components/Flash';
import { publicEventBySlug, ticketTypesWithState } from '@/lib/services/events';
import { loungeAvailability } from '@/lib/services/lounges';
import { orgBySlug } from '@/lib/services/orgs';
import { onlinePaymentsEnabled } from '@/lib/payments';
import { ticketFee, loungeFee } from '@/lib/pricing';
import { zl } from '@/lib/money';
import { env } from '@/lib/env';
import { fmtDate, fmtTime } from '@/lib/time';
import { pickLang, t } from '@/lib/i18n';
import { buyTicketsAction, reserveLoungeAction } from './actions';

type Params = { org: string; event: string };

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { org, event } = await params;
  const e = await publicEventBySlug(org, event);
  return e ? { title: `${e.name} — ${e.org_name}`, description: e.description.slice(0, 160) || `Bilety i loże: ${e.name}` } : {};
}

function BuyerFields({ L, lang }: { L: (typeof t)['pl'] | (typeof t)['en']; lang: string }) {
  return (
    <>
      <div className="form-grid">
        <div className="field"><label>{L.name}</label><input name="name" autoComplete="name" required minLength={3} /></div>
        <div className="field"><label>{L.email}</label><input name="email" type="email" autoComplete="email" required /></div>
        <div className="field"><label>{L.phone}</label><input name="phone" type="tel" autoComplete="tel" /></div>
      </div>
      <label className="check field"><input type="checkbox" name="terms" required /> <span>{L.terms} <Link href="/regulamin" target="_blank">{lang === 'en' ? 'Terms' : 'Regulamin'}</Link></span></label>
      <label className="check field"><input type="checkbox" name="marketing" /> <span>{L.marketing}</span></label>
    </>
  );
}

export default async function EventPublicPage({ params, searchParams }: { params: Promise<Params>; searchParams: Promise<{ lang?: string; ok?: string; blad?: string; loza?: string; p?: string }> }) {
  const { org: orgSlug, event: eventSlug } = await params;
  const sp = await searchParams;
  const [event, org] = await Promise.all([publicEventBySlug(orgSlug, eventSlug), orgBySlug(orgSlug)]);
  if (!event || !org) notFound();
  const lang = pickLang(sp.lang, (await headers()).get('accept-language'));
  const L = t[lang];
  const [types, lounges] = await Promise.all([ticketTypesWithState(event.id), loungeAvailability(org.id, event.id)]);
  const payments = onlinePaymentsEnabled(org.payment_provider);
  const ended = new Date(event.ends_at).getTime() < Date.now();
  const open = event.status === 'published' && !ended;
  const sellable = types.filter((tt) => tt.active && tt.state !== 'inactive');
  const canBuy = open && sellable.some((tt) => tt.state === 'on_sale' && (tt.price === 0 || payments));
  const ref = sp.p ?? (await cookies()).get(`ref_${org.slug}`)?.value ?? '';
  const hidden = (
    <>
      <input type="hidden" name="eventId" value={event.id} /><input type="hidden" name="orgSlug" value={org.slug} />
      <input type="hidden" name="eventSlug" value={event.slug} /><input type="hidden" name="lang" value={lang} />
      {ref && <input type="hidden" name="p" value={ref} />}
    </>
  );
  const stateLabel: Record<string, string> = { sold_out: L.soldOut, ended: L.ended, upcoming: L.upcoming, waiting: L.waiting };
  const jsonLd = {
    '@context': 'https://schema.org', '@type': 'Event', name: event.name, startDate: new Date(event.starts_at).toISOString(),
    endDate: new Date(event.ends_at).toISOString(), eventStatus: event.status === 'cancelled' ? 'https://schema.org/EventCancelled' : 'https://schema.org/EventScheduled',
    eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode', description: event.description,
    location: { '@type': 'Place', name: event.venue_name ?? org.name, address: org.address ?? org.city ?? '' },
    organizer: { '@type': 'Organization', name: org.name, url: `${env.appUrl}/k/${org.slug}` },
    offers: sellable.filter((tt) => tt.state === 'on_sale').map((tt) => ({
      '@type': 'Offer', name: tt.name, price: (tt.price / 100).toFixed(2), priceCurrency: 'PLN', availability: 'https://schema.org/InStock',
      url: `${env.appUrl}/k/${org.slug}/e/${event.slug}`,
    })),
  };

  return (
    <main className="wrap" style={{ maxWidth: 860 }}>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd).replace(/</g, '\\u003c') }} />
      <div className="row between">
        <Link href={`/k/${org.slug}${lang === 'en' ? '?lang=en' : ''}`} className="brand">{org.name}</Link>
        <nav className="row" style={{ gap: 8 }}>
          <Link href={`/k/${org.slug}/e/${event.slug}`} className={lang === 'pl' ? 'tag accent' : 'tag'}>PL</Link>
          <Link href={`/k/${org.slug}/e/${event.slug}?lang=en`} className={lang === 'en' ? 'tag accent' : 'tag'}>EN</Link>
        </nav>
      </div>
      <section className="hero">
        <div className="event-date">{fmtDate(event.starts_at)} · {fmtTime(event.starts_at)}–{fmtTime(event.ends_at)}</div>
        <h1>{event.name}</h1>
        <p className="soft">
          {event.venue_name ?? org.name}{org.address ? `, ${org.address}` : ''}
          {event.min_age ? <> · <span className="tag">{L.age} {event.min_age}+</span></> : null}
        </p>
        {event.status === 'cancelled' && <div className="flash bad">{L.cancelled}</div>}
        {event.description && <p style={{ whiteSpace: 'pre-line' }}>{event.description}</p>}
      </section>
      {sp.loza === 'wyslana' && <div className="flash ok">{L.loungeSent}</div>}
      <Flash sp={sp} />

      <section id="bilety" className="card">
        <h2>{L.tickets}</h2>
        {sellable.length === 0 && <p className="soft">{L.atDoor}</p>}
        <form action={buyTicketsAction}>
          {hidden}
          {sellable.map((tt) => {
            const purchasable = open && tt.state === 'on_sale' && (tt.price === 0 || payments);
            const fee = org.fee_payer === 'buyer' ? ticketFee(tt.price, org.plan) : 0;
            return (
              <div key={tt.id} className="ticket-line">
                <div>
                  <strong>{tt.name}</strong>{tt.group_size > 1 && <span className="muted"> · {tt.group_size} os.</span>}
                  <div className="muted" style={{ fontSize: '.85rem' }}>{tt.tier_group}{!purchasable && ` · ${tt.state === 'on_sale' ? L.atDoor : stateLabel[tt.state] ?? ''}`}</div>
                </div>
                <div className="price num" style={{ textAlign: 'right' }}>
                  <strong>{zl(tt.price)}</strong>
                  {fee > 0 && <div className="muted" style={{ fontSize: '.8rem' }}>+ {zl(fee)} {L.fee}</div>}
                </div>
                {purchasable ? (
                  <select name={`qty_${tt.id}`} aria-label={`${tt.name}`} defaultValue="0">
                    {Array.from({ length: Math.min(10, tt.remaining) + 1 }, (_, i) => <option key={i} value={i}>{i}</option>)}
                  </select>
                ) : <span />}
              </div>
            );
          })}
          {canBuy && (
            <div style={{ marginTop: 16 }}>
              <BuyerFields L={L} lang={lang} />
              <div className="form-grid">
                <div className="field"><label>{L.discount}</label><input name="discount" autoCapitalize="characters" /></div>
              </div>
              <button className="block" type="submit">{L.buy}</button>
              {payments && <p className="muted" style={{ fontSize: '.85rem', marginTop: 8 }}>{L.payWith}</p>}
            </div>
          )}
        </form>
      </section>

      {open && lounges.length > 0 && (
        <section id="loze" className="card">
          <h2>{L.lounges}</h2>
          <form action={reserveLoungeAction}>
            {hidden}
            <p className="soft">{L.loungePick}</p>
            <div className="floor" role="radiogroup" aria-label={L.loungePick}>
              <div className="stage">DJ</div><div className="bar-area">bar</div>
              {lounges.map((l) => l.taken ? (
                <div key={l.id} className="spot taken" style={{ left: `${l.map_x}%`, top: `${l.map_y}%`, width: `${l.map_w}%`, height: `${l.map_h}%` }}>
                  <strong>{l.name}</strong><span>{L.taken}</span>
                </div>
              ) : (
                <label key={l.id} className="spot" style={{ left: `${l.map_x}%`, top: `${l.map_y}%`, width: `${l.map_w}%`, height: `${l.map_h}%` }}>
                  <input type="radio" name="loungeId" value={l.id} required />
                  <strong>{l.name}</strong><span>{zl(l.base_price)}</span>
                </label>
              ))}
            </div>
            <ul style={{ listStyle: 'none', padding: 0, margin: '12px 0 0' }}>
              {lounges.filter((l) => !l.taken).map((l) => {
                const prepay = Math.ceil((l.base_price * l.prepay_percent) / 100);
                return (
                  <li key={l.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--line)' }}>
                    <div className="row between"><strong>{l.name} <span className="muted" style={{ fontWeight: 400 }}>· {l.zone}</span></strong><strong>{zl(l.base_price)}</strong></div>
                    <div className="muted" style={{ fontSize: '.85rem' }}>
                      {l.capacity} {L.inPrice}{l.max_capacity > l.capacity && ` (+${zl(l.extra_person_price)}/os., max ${l.max_capacity})`}
                      {payments && l.prepay_percent > 0 ? ` · ${L.prepay}: ${zl(prepay)}${org.fee_payer === 'buyer' ? ` + ${zl(loungeFee(prepay, org.plan))}` : ''}` : l.min_spend ? ` · ${L.minSpend} ${zl(l.min_spend)}` : ''}
                    </div>
                  </li>
                );
              })}
            </ul>
            <div style={{ marginTop: 16 }}>
              <div className="form-grid">
                <div className="field"><label>{L.persons}</label><input name="persons" type="number" min={1} max={20} defaultValue={6} required /></div>
                <div className="field" style={{ gridColumn: 'span 2' }}><label>{L.notes}</label><input name="notes" maxLength={500} /></div>
              </div>
              <BuyerFields L={L} lang={lang} />
              <button className="block" type="submit">{payments ? L.loungeCta : L.loungeRequest}</button>
            </div>
          </form>
        </section>
      )}
      <footer className="site"><Link href="/regulamin">Regulamin</Link> · <Link href="/prywatnosc">Prywatność</Link></footer>
    </main>
  );
}
