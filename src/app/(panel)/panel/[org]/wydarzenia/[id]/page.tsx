import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Flash } from '@/components/Flash';
import { EventTabs, PanelNav } from '@/components/PanelNav';
import { requireOrg } from '@/lib/session';
import { getEvent, ticketTypesWithState } from '@/lib/services/events';
import { discountCodes } from '@/lib/services/orgs';
import { promotersForOrg } from '@/lib/services/promoters';
import { onlinePaymentsEnabled } from '@/lib/payments';
import { ticketFee } from '@/lib/pricing';
import { zl } from '@/lib/money';
import { env } from '@/lib/env';
import { fmtDateTime, toLocalInput } from '@/lib/time';
import { addTicketTypeAction, discountAction, setStatusAction, ticketTypeAction, updateEventAction } from './actions';

const STATE: Record<string, [string, string]> = {
  on_sale: ['w sprzedaży', 'ok'], sold_out: ['wyprzedana', 'bad'], ended: ['zakończona', ''], upcoming: ['od ' , 'warn'],
  waiting: ['czeka na swoją kolej', ''], inactive: ['wyłączona', ''],
};

export default async function EventPage({ params, searchParams }: { params: Promise<{ org: string; id: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { org: slug, id } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug);
  const event = await getEvent(org.id, id);
  if (!event) notFound();
  const [types, codes, promoters] = await Promise.all([ticketTypesWithState(event.id), discountCodes(org.id, event.id), promotersForOrg(org.id)]);
  const publicUrl = `${env.appUrl}/k/${org.slug}/e/${event.slug}`;
  const hidden = (<><input type="hidden" name="org" value={org.slug} /><input type="hidden" name="event" value={event.id} /></>);
  const payments = onlinePaymentsEnabled(org.payment_provider);

  return (
    <>
      <PanelNav org={org} active="wydarzenia" userName={user.name} />
      <main className="wrap">
        <div className="row between">
          <div>
            <div className="event-date">{fmtDateTime(event.starts_at)}</div>
            <h1 style={{ margin: '4px 0' }}>{event.name}</h1>
          </div>
          <div className="row">
            {event.status !== 'published' && <form action={setStatusAction}>{hidden}<input type="hidden" name="status" value="published" /><button>Opublikuj</button></form>}
            {event.status === 'published' && <form action={setStatusAction}>{hidden}<input type="hidden" name="status" value="draft" /><button className="ghost">Ukryj</button></form>}
            {event.status !== 'cancelled' && <form action={setStatusAction}>{hidden}<input type="hidden" name="status" value="cancelled" /><button className="danger">Odwołaj</button></form>}
          </div>
        </div>
        <EventTabs orgSlug={org.slug} eventId={event.id} active="przeglad" />
        <Flash sp={sp} />

        {event.status === 'published' && (
          <div className="card">
            <h3>Linki sprzedażowe</h3>
            <p className="soft" style={{ marginBottom: 6 }}>Strona imprezy (do bio na Instagramie i wydarzenia na Facebooku):</p>
            <code style={{ wordBreak: 'break-all' }}><Link href={publicUrl}>{publicUrl}</Link></code>
            {promoters.filter((p) => p.active).length > 0 && (
              <details style={{ marginTop: 10 }}>
                <summary className="soft" style={{ cursor: 'pointer' }}>Linki promotorów</summary>
                <ul>{promoters.filter((p) => p.active).map((p) => <li key={p.id}><strong>{p.name}</strong>: <code>{publicUrl}?p={p.code}</code></li>)}</ul>
              </details>
            )}
          </div>
        )}

        <div className="card">
          <h2>Pule biletów</h2>
          {!payments && <p className="flash info">Płatności online są wyłączone: w sprzedaży online będą tylko pule bezpłatne (np. wejściówki z zaproszeniem). Płatne bilety goście kupią na bramce.</p>}
          <p className="soft">W każdej grupie sprzedaje się najpierw pierwsza pula; gdy się wyprzeda albo skończy jej termin, w sprzedaży jest kolejna (early bird → I pula → II pula).</p>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Grupa</th><th>Pula</th><th className="num">Cena</th><th className="num">Opłata</th><th className="num">Sprzedane</th><th className="num">W koszykach</th><th>Wielkość puli</th><th>Stan</th><th /></tr></thead>
              <tbody>
                {types.map((t) => (
                  <tr key={t.id}>
                    <td>{t.tier_group}</td>
                    <td>{t.name}{t.group_size > 1 && <span className="muted"> · {t.group_size} os.</span>}{t.sales_end && <div className="muted">do {fmtDateTime(t.sales_end)}</div>}</td>
                    <td className="num">{zl(t.price)}</td>
                    <td className="num muted">{zl(ticketFee(t.price, org.plan))}</td>
                    <td className="num">{t.sold}</td>
                    <td className="num">{t.held}</td>
                    <td>
                      <form action={ticketTypeAction} className="row" style={{ flexWrap: 'nowrap', gap: 6 }}>
                        {hidden}<input type="hidden" name="id" value={t.id} />
                        <input name="quantity" type="number" min={0} defaultValue={t.quantity} style={{ width: 90, minHeight: 32, padding: '4px 8px' }} />
                        <button className="ghost small">Zmień</button>
                      </form>
                    </td>
                    <td><span className={`tag ${STATE[t.state][1]}`}>{t.state === 'upcoming' && t.sales_start ? `od ${fmtDateTime(t.sales_start)}` : STATE[t.state][0]}</span></td>
                    <td>
                      <form action={ticketTypeAction}>{hidden}<input type="hidden" name="id" value={t.id} /><input type="hidden" name="active" value={t.active ? '0' : '1'} /><button className="ghost small">{t.active ? 'Wyłącz' : 'Włącz'}</button></form>
                    </td>
                  </tr>
                ))}
                {types.length === 0 && <tr><td colSpan={9} className="muted">Dodaj pierwszą pulę poniżej.</td></tr>}
              </tbody>
            </table>
          </div>
          <form action={addTicketTypeAction} style={{ marginTop: 16 }}>
            {hidden}
            <div className="form-grid">
              <div className="field"><label>Grupa</label><input name="tierGroup" defaultValue="Wejście" /></div>
              <div className="field"><label>Nazwa puli</label><input name="name" placeholder="Early bird" required /></div>
              <div className="field"><label>Cena (zł)</label><input name="price" inputMode="decimal" placeholder="35" required /></div>
              <div className="field"><label>Liczba biletów</label><input name="quantity" type="number" min={0} defaultValue={100} required /></div>
              <div className="field"><label>Osób na bilet</label><input name="groupSize" type="number" min={1} max={20} defaultValue={1} /></div>
              <div className="field"><label>Sprzedaż od (opcj.)</label><input name="salesStart" type="datetime-local" /></div>
              <div className="field"><label>Sprzedaż do (opcj.)</label><input name="salesEnd" type="datetime-local" /></div>
            </div>
            <button type="submit">Dodaj pulę</button>
          </form>
        </div>

        <div className="grid grid-2">
          <form action={updateEventAction} className="card">
            {hidden}
            <h2>Szczegóły imprezy</h2>
            <div className="field"><label>Nazwa</label><input name="name" defaultValue={event.name} required /></div>
            <div className="form-grid">
              <div className="field"><label>Początek</label><input name="startsAt" type="datetime-local" defaultValue={toLocalInput(event.starts_at)} required /></div>
              <div className="field"><label>Koniec</label><input name="endsAt" type="datetime-local" defaultValue={toLocalInput(event.ends_at)} required /></div>
              <div className="field"><label>Limit osób</label><input name="capacity" type="number" min={1} defaultValue={event.capacity ?? ''} /></div>
              <div className="field"><label>Wiek</label><select name="minAge" defaultValue={event.min_age ?? ''}><option value="">bez limitu</option><option value="16">16+</option><option value="18">18+</option><option value="21">21+</option></select></div>
            </div>
            <div className="field"><label>Miejsce</label><input name="venueName" defaultValue={event.venue_name ?? ''} /></div>
            <div className="field"><label>Opis</label><textarea name="description" defaultValue={event.description} rows={4} /></div>
            <button type="submit">Zapisz</button>
          </form>

          <div className="card">
            <h2>Kody rabatowe</h2>
            <p className="soft">Zamiast „panie za darmo” (ryzyko prawne: nierówne traktowanie) używaj promocji dla wszystkich: kod dla studentów, pierwsze 100 osób, lista do określonej godziny.</p>
            <table>
              <tbody>
                {codes.map((c) => (
                  <tr key={c.id} className={c.active ? '' : 'dim'}>
                    <td><code>{c.code}</code>{!c.event_id && <span className="muted"> (wszystkie imprezy)</span>}</td>
                    <td>−{c.percent_off}%</td>
                    <td className="num">{c.used}{c.max_uses ? ` / ${c.max_uses}` : ''}</td>
                    <td><form action={discountAction}>{hidden}<input type="hidden" name="id" value={c.id} /><input type="hidden" name="active" value={c.active ? '0' : '1'} /><button className="ghost small">{c.active ? 'Wyłącz' : 'Włącz'}</button></form></td>
                  </tr>
                ))}
              </tbody>
            </table>
            <form action={discountAction} className="form-grid" style={{ marginTop: 12, alignItems: 'end' }}>
              {hidden}
              <div className="field"><label>Kod</label><input name="code" placeholder="STUDENT" required /></div>
              <div className="field"><label>Rabat %</label><input name="percentOff" type="number" min={1} max={100} defaultValue={20} required /></div>
              <div className="field"><label>Limit użyć</label><input name="maxUses" type="number" min={1} placeholder="bez limitu" /></div>
              <div className="field"><button className="block">Dodaj kod</button></div>
            </form>
          </div>
        </div>
      </main>
    </>
  );
}
