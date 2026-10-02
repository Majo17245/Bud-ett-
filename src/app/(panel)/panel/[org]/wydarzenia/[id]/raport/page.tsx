import { notFound } from 'next/navigation';
import { EventTabs, PanelNav } from '@/components/PanelNav';
import { requireOrg } from '@/lib/session';
import { getEvent } from '@/lib/services/events';
import { liveReport } from '@/lib/services/reports';
import { zl } from '@/lib/money';
import { fmtTime } from '@/lib/time';
import { LiveRefresh } from './LiveRefresh';

const KIND: Record<string, string> = { ticket: 'Bilety online', guest: 'Listy gości', lounge: 'Loże', external: 'Inne platformy', licznik: 'Licznik / kasa' };
const PROBLEM: Record<string, string> = { duplicate: 'ponowny skan', invalid: 'nieznany kod', void: 'unieważniony', too_late: 'lista po czasie' };

export default async function ReportPage({ params }: { params: Promise<{ org: string; id: string }> }) {
  const { org: slug, id } = await params;
  const { user, org } = await requireOrg(slug);
  const event = await getEvent(org.id, id);
  if (!event) notFound();
  const r = await liveReport(org.id, event.id);
  const capacity = event.capacity ?? org.capacity;
  const maxSlot = Math.max(1, ...r.timeline.map((t) => t.persons));
  const online = r.sales.gross;

  return (
    <>
      <PanelNav org={org} active="wydarzenia" userName={user.name} />
      <main className="wrap">
        <div className="row between"><h1>{event.name}</h1><LiveRefresh /></div>
        <EventTabs orgSlug={org.slug} eventId={event.id} active="raport" />
        <div className="stats">
          <div className="stat"><b>{r.door.inside}{capacity ? <small className="muted" style={{ fontSize: '1rem' }}> / {capacity}</small> : null}</b><span>w sali teraz</span>
            {capacity ? <div className="bar"><i style={{ width: `${Math.min(100, (r.door.inside / capacity) * 100)}%`, background: r.door.inside > capacity * 0.95 ? 'var(--bad)' : undefined }} /></div> : null}
          </div>
          <div className="stat"><b>{r.door.entered}</b><span>weszło łącznie</span></div>
          <div className="stat"><b>{r.sales.tickets}</b><span>biletów sprzedanych online</span></div>
          <div className="stat"><b>{zl(online)}</b><span>sprzedaż online (bez opłat)</span></div>
          <div className="stat"><b>{r.lounges.arrived}/{r.lounges.booked}</b><span>loże: przyszli / zarezerwowane</span></div>
        </div>

        <div className="grid grid-2">
          <div className="card">
            <h2>Wejścia co 15 minut</h2>
            {r.timeline.length === 0 ? <p className="muted">Jeszcze nikt nie wszedł.</p> : (
              <>
                <div className="spark" aria-label="Wykres wejść">
                  {r.timeline.map((t) => <div key={String(t.slot)} title={`${fmtTime(t.slot)}: ${t.persons} os.`} style={{ height: `${(t.persons / maxSlot) * 100}%` }} />)}
                </div>
                <div className="row between muted" style={{ fontSize: '.8rem' }}><span>{fmtTime(r.timeline[0].slot)}</span><span>{fmtTime(r.timeline[r.timeline.length - 1].slot)}</span></div>
              </>
            )}
            <h3 style={{ marginTop: 16 }}>Kanały wejścia</h3>
            <table><tbody>{r.entriesByKind.map((k) => <tr key={k.kind}><td>{KIND[k.kind] ?? k.kind}</td><td className="num">{k.persons}</td></tr>)}</tbody></table>
            {r.problems.length > 0 && (
              <p className="muted" style={{ marginTop: 12 }}>Odrzucone skany: {r.problems.map((p) => `${PROBLEM[p.result] ?? p.result} ${p.n}`).join(', ')}</p>
            )}
          </div>
          <div className="card table-wrap">
            <h2>Pule biletów</h2>
            <table>
              <thead><tr><th>Pula</th><th className="num">Sprzedane</th><th className="num">Weszło</th></tr></thead>
              <tbody>{r.byType.map((t) => <tr key={t.id}><td>{t.name} <span className="muted">· {zl(t.price)}</span></td><td className="num">{t.sold}/{t.quantity}</td><td className="num">{t.entered}</td></tr>)}</tbody>
            </table>
            {r.external.length > 0 && (
              <>
                <h3 style={{ marginTop: 16 }}>Inne platformy</h3>
                <table><tbody>{r.external.map((x) => <tr key={x.source}><td>{x.source.toUpperCase()}</td><td className="num">{x.entered}/{x.total}</td></tr>)}</tbody></table>
              </>
            )}
            <h3 style={{ marginTop: 16 }}>Loże</h3>
            <p className="soft">Zarezerwowane {r.lounges.booked} (wartość {zl(r.lounges.value)}, przedpłaty {zl(r.lounges.prepaid)}), prośby do obsłużenia: {r.lounges.requested}, nie przyszli: {r.lounges.no_show}.</p>
          </div>
        </div>

        <div className="grid grid-2">
          <div className="card table-wrap">
            <h2>Listy gości</h2>
            <table>
              <thead><tr><th>Lista</th><th className="num">Na liście</th><th className="num">Weszło</th></tr></thead>
              <tbody>{r.lists.map((l) => <tr key={l.name}><td>{l.name}{l.promoter_name && <span className="muted"> · {l.promoter_name}</span>}</td><td className="num">{l.listed}/{l.capacity}</td><td className="num">{l.entered}</td></tr>)}</tbody>
            </table>
          </div>
          <div className="card table-wrap">
            <h2>Promotorzy tej nocy</h2>
            <table>
              <thead><tr><th>Promotor</th><th className="num">Bilety</th><th className="num">Z list</th><th className="num">Prowizja</th></tr></thead>
              <tbody>{r.promoters.map((p) => <tr key={p.promoter_id}><td>{p.name}</td><td className="num">{p.tickets}</td><td className="num">{p.guests_entered}/{p.guests_listed}</td><td className="num">{zl(p.commission)}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      </main>
    </>
  );
}
