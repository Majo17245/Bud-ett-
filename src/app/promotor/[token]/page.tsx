import { notFound } from 'next/navigation';
import { Flash } from '@/components/Flash';
import { promoterByToken, promoterStats } from '@/lib/services/promoters';
import { publicEvents } from '@/lib/services/events';
import { entriesForList, listsForEvent } from '@/lib/services/lists';
import { zl } from '@/lib/money';
import { env } from '@/lib/env';
import { fmtDateTime, fmtTime } from '@/lib/time';
import { promoterAddGuestsAction, promoterVoidGuestAction } from './actions';

export const metadata = { title: 'Panel promotora', robots: { index: false } };

export default async function PromoterPanel({ params, searchParams }: { params: Promise<{ token: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { token } = await params;
  const sp = await searchParams;
  const p = await promoterByToken(token);
  if (!p) notFound();
  const [events, ranking] = await Promise.all([publicEvents(p.org_id), promoterStats(p.org_id)]);
  const me = ranking.find((r) => r.promoter_id === p.id);
  const position = ranking.findIndex((r) => r.promoter_id === p.id) + 1;
  const perEvent = await Promise.all(events.map(async (e) => {
    const lists = await listsForEvent(e.id, p.id);
    const withEntries = await Promise.all(lists.map(async (l) => ({ ...l, entries: await entriesForList(l.id) })));
    const [stats] = (await promoterStats(p.org_id, e.id)).filter((s) => s.promoter_id === p.id);
    return { e, lists: withEntries, stats };
  }));

  return (
    <main className="wrap" style={{ maxWidth: 860 }}>
      <span className="brand">{p.org_name}</span>
      <h1 style={{ marginTop: 12 }}>Cześć, {p.name}!</h1>
      <Flash sp={sp} />
      <div className="stats">
        <div className="stat"><b>#{position}</b><span>miejsce w rankingu z {ranking.length}</span></div>
        <div className="stat"><b>{me?.tickets ?? 0}</b><span>biletów z Twoich linków</span></div>
        <div className="stat"><b>{me?.guests_entered ?? 0}</b><span>gości z Twoich list weszło</span></div>
        <div className="stat"><b>{zl(me?.commission ?? 0)}</b><span>prowizja łącznie</span></div>
      </div>
      {perEvent.map(({ e, lists, stats }) => {
        const link = `${env.appUrl}/k/${p.org_slug}/e/${e.slug}?p=${p.code}`;
        return (
          <section key={e.id} className="card">
            <div className="event-date">{fmtDateTime(e.starts_at)}</div>
            <h2 style={{ margin: '4px 0 8px' }}>{e.name}</h2>
            <p className="soft" style={{ marginBottom: 4 }}>Twój link sprzedażowy:</p>
            <code style={{ wordBreak: 'break-all' }}>{link}</code>
            <p className="muted" style={{ marginTop: 8 }}>
              Ta noc: {stats?.tickets ?? 0} biletów · {stats?.guests_listed ?? 0} na listach · {stats?.guests_entered ?? 0} weszło · prowizja {zl(stats?.commission ?? 0)}
            </p>
            {lists.map((l) => (
              <div key={l.id} id={`lista-${l.id}`} style={{ marginTop: 16 }}>
                <h3>{l.name} <span className="muted">— {l.used}/{l.capacity}{l.entry_until ? `, wejście do ${fmtTime(l.entry_until)}` : ''}</span></h3>
                <div className="bar"><i style={{ width: `${Math.min(100, (l.used / l.capacity) * 100)}%` }} /></div>
                <form action={promoterAddGuestsAction} style={{ marginTop: 10 }}>
                  <input type="hidden" name="token" value={token} /><input type="hidden" name="listId" value={l.id} />
                  <textarea name="guests" rows={3} placeholder={'Anna Nowak\nJan Kowalski +1'} required />
                  <div className="row" style={{ marginTop: 8 }}>
                    <input name="phone" type="tel" placeholder="telefon (przy jednej osobie)" style={{ flex: 1, minWidth: 180 }} />
                    <button>Dopisz</button>
                  </div>
                </form>
                <table style={{ marginTop: 8 }}>
                  <tbody>
                    {l.entries.filter((g) => g.status === 'invited').map((g) => (
                      <tr key={g.id}>
                        <td>{g.full_name}{g.plus_ones ? ` +${g.plus_ones}` : ''}</td>
                        <td><a href={`${env.appUrl}/zaproszenie/${g.code}`} target="_blank" rel="noreferrer">zaproszenie</a></td>
                        <td>{g.checked_in_at ? <span className="tag ok">wszedł {fmtTime(g.checked_in_at)}</span> : (
                          <form action={promoterVoidGuestAction}>
                            <input type="hidden" name="token" value={token} /><input type="hidden" name="eventId" value={e.id} /><input type="hidden" name="entryId" value={g.id} />
                            <button className="danger small">Usuń</button>
                          </form>
                        )}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
            {lists.length === 0 && <p className="muted">Nie masz listy na tę imprezę — poproś managera o jej utworzenie.</p>}
          </section>
        );
      })}
      {events.length === 0 && <p className="soft">Brak nadchodzących imprez.</p>}
    </main>
  );
}
