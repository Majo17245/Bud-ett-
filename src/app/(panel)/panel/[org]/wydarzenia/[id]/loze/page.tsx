import { notFound } from 'next/navigation';
import { Flash } from '@/components/Flash';
import { EventTabs, PanelNav } from '@/components/PanelNav';
import { requireOrg } from '@/lib/session';
import { getEvent } from '@/lib/services/events';
import { loungeAvailability, reservationsForEvent } from '@/lib/services/lounges';
import { zl } from '@/lib/money';
import { fmtDateTime } from '@/lib/time';
import { addReservationAction, reservationStatusAction } from '../actions';

const STATUS: Record<string, [string, string]> = {
  requested: ['prośba — zadzwoń', 'warn'], pending_payment: ['czeka na płatność', 'warn'], confirmed: ['potwierdzona', 'ok'],
  paid: ['opłacona', 'ok'], cancelled: ['anulowana', ''], no_show: ['nie przyszli', 'bad'],
};
const SOURCE: Record<string, string> = { web: 'strona', phone: 'telefon', dm: 'DM', panel: 'panel' };

export default async function EventLoungesPage({ params, searchParams }: { params: Promise<{ org: string; id: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { org: slug, id } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug);
  const event = await getEvent(org.id, id);
  if (!event) notFound();
  const [lounges, reservations] = await Promise.all([loungeAvailability(org.id, event.id), reservationsForEvent(event.id)]);
  const hidden = (<><input type="hidden" name="org" value={org.slug} /><input type="hidden" name="event" value={event.id} /></>);
  const statusForm = (rid: string, status: string, label: string, cls = 'ghost') => (
    <form action={reservationStatusAction} className="inline">{hidden}<input type="hidden" name="id" value={rid} /><input type="hidden" name="status" value={status} /><button className={`${cls} small`}>{label}</button></form>
  );

  return (
    <>
      <PanelNav org={org} active="wydarzenia" userName={user.name} />
      <main className="wrap">
        <h1>{event.name}</h1>
        <EventTabs orgSlug={org.slug} eventId={event.id} active="loze" />
        <Flash sp={sp} />
        {lounges.length === 0 && <p className="flash info">Najpierw dodaj loże w zakładce „Loże i sala”.</p>}
        <div className="grid grid-2">
          <div className="card">
            <h2>Sala tej nocy</h2>
            <div className="floor">
              <div className="stage">scena / DJ</div><div className="bar-area">bar</div>
              {lounges.map((l) => (
                <div key={l.id} className={`spot ${l.taken ? 'taken' : l.pending_requests ? 'pending' : ''}`} style={{ left: `${l.map_x}%`, top: `${l.map_y}%`, width: `${l.map_w}%`, height: `${l.map_h}%` }}>
                  <strong>{l.name}</strong><span>{l.taken ? 'zajęta' : l.pending_requests ? `${l.pending_requests} prośby` : 'wolna'}</span>
                </div>
              ))}
            </div>
          </div>
          <form action={addReservationAction} className="card">
            {hidden}
            <h2>Rezerwacja z telefonu lub DM</h2>
            <div className="form-grid">
              <div className="field"><label>Loża</label><select name="loungeId" required>{lounges.filter((l) => !l.taken).map((l) => <option key={l.id} value={l.id}>{l.name} ({l.capacity}–{l.max_capacity} os., {zl(l.base_price)})</option>)}</select></div>
              <div className="field"><label>Osób</label><input name="persons" type="number" min={1} defaultValue={6} required /></div>
              <div className="field"><label>Nazwisko</label><input name="name" required /></div>
              <div className="field"><label>Telefon</label><input name="phone" type="tel" /></div>
              <div className="field"><label>Źródło</label><select name="source"><option value="phone">telefon</option><option value="dm">DM (Instagram/WhatsApp)</option><option value="panel">inne</option></select></div>
              <div className="field"><label>Notatka</label><input name="notes" placeholder="np. butelka na start, urodziny" /></div>
            </div>
            <button>Zarezerwuj</button>
          </form>
        </div>
        <div className="card table-wrap">
          <h2>Rezerwacje</h2>
          <table>
            <thead><tr><th>Loża</th><th>Gość</th><th className="num">Osób</th><th className="num">Wartość</th><th className="num">Przedpłata</th><th>Status</th><th>Źródło</th><th>Akcje</th></tr></thead>
            <tbody>
              {reservations.map((r) => (
                <tr key={r.id} className={['cancelled'].includes(r.status) ? 'dim' : ''}>
                  <td><strong>{r.lounge_name}</strong></td>
                  <td>{r.name}<div className="muted">{r.phone ?? r.email}{r.notes ? ` · ${r.notes}` : ''}</div></td>
                  <td className="num">{r.persons}</td>
                  <td className="num">{zl(r.total_price)}</td>
                  <td className="num">{r.status === 'paid' ? zl(r.prepay_amount) : '—'}</td>
                  <td><span className={`tag ${STATUS[r.status][1]}`}>{STATUS[r.status][0]}</span>{r.checked_in_at && <div className="muted">przyszli {fmtDateTime(r.checked_in_at)}</div>}</td>
                  <td>{SOURCE[r.source]}{r.promoter_name ? ` · ${r.promoter_name}` : ''}</td>
                  <td>
                    <div className="row" style={{ gap: 4 }}>
                      {r.status === 'requested' && statusForm(r.id, 'confirmed', 'Potwierdź', '')}
                      {['requested', 'confirmed'].includes(r.status) && statusForm(r.id, 'cancelled', 'Anuluj', 'danger')}
                      {['confirmed', 'paid'].includes(r.status) && !r.checked_in_at && statusForm(r.id, 'no_show', 'Nie przyszli')}
                    </div>
                  </td>
                </tr>
              ))}
              {reservations.length === 0 && <tr><td colSpan={8} className="muted">Brak rezerwacji.</td></tr>}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
