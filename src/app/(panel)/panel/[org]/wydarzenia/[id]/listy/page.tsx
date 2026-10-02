import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Flash } from '@/components/Flash';
import { EventTabs, PanelNav } from '@/components/PanelNav';
import { requireOrg } from '@/lib/session';
import { getEvent } from '@/lib/services/events';
import { entriesForList, listsForEvent } from '@/lib/services/lists';
import { promotersForOrg } from '@/lib/services/promoters';
import { env } from '@/lib/env';
import { fmtTime, toLocalInput } from '@/lib/time';
import { addGuestsAction, createListAction, updateListAction, voidGuestAction } from '../actions';

export default async function ListsPage({ params, searchParams }: { params: Promise<{ org: string; id: string }>; searchParams: Promise<{ ok?: string; blad?: string; lista?: string }> }) {
  const { org: slug, id } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug);
  const event = await getEvent(org.id, id);
  if (!event) notFound();
  const [lists, promoters] = await Promise.all([listsForEvent(event.id), promotersForOrg(org.id)]);
  const selected = lists.find((l) => l.id === sp.lista) ?? lists[0];
  const entries = selected ? await entriesForList(selected.id) : [];
  const hidden = (<><input type="hidden" name="org" value={org.slug} /><input type="hidden" name="event" value={event.id} /></>);
  const defaultUntil = new Date(new Date(event.starts_at).getTime() + 2 * 3600_000);
  const base = `/panel/${org.slug}/wydarzenia/${event.id}`;

  return (
    <>
      <PanelNav org={org} active="wydarzenia" userName={user.name} />
      <main className="wrap">
        <h1>{event.name}</h1>
        <EventTabs orgSlug={org.slug} eventId={event.id} active="listy" />
        <Flash sp={sp} />
        <div className="grid" style={{ gridTemplateColumns: 'minmax(240px, 320px) 1fr', alignItems: 'start' }}>
          <aside>
            {lists.map((l) => (
              <Link key={l.id} href={`${base}/listy?lista=${l.id}`} className="event-card" style={{ marginBottom: 8, borderColor: l.id === selected?.id ? 'var(--accent)' : undefined }}>
                <div className="row between"><strong>{l.name}</strong><span className="muted">{l.used}/{l.capacity}</span></div>
                <div className="muted" style={{ fontSize: '.85rem' }}>
                  {l.promoter_name ? `promotor: ${l.promoter_name}` : 'lista klubu'}{l.entry_until ? ` · wejście do ${fmtTime(l.entry_until)}` : ''} · weszło {l.entered}
                </div>
                <div className="bar"><i style={{ width: `${Math.min(100, (l.used / l.capacity) * 100)}%` }} /></div>
              </Link>
            ))}
            <form action={createListAction} className="card" style={{ marginTop: 12 }}>
              {hidden}
              <h3>Nowa lista</h3>
              <div className="field"><label>Nazwa</label><input name="name" placeholder="Lista DJ-a" required /></div>
              <div className="field"><label>Limit osób</label><input name="capacity" type="number" min={1} defaultValue={30} required /></div>
              <div className="field"><label>Wejście z listy do</label><input name="entryUntil" type="datetime-local" defaultValue={toLocalInput(defaultUntil)} /></div>
              <div className="field">
                <label>Promotor</label>
                <select name="promoterId" defaultValue=""><option value="">— lista klubu —</option>{promoters.filter((p) => p.active).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select>
              </div>
              <button className="block">Utwórz listę</button>
            </form>
          </aside>

          <section>
            {!selected && <p className="soft">Utwórz pierwszą listę gości. Każda osoba dostaje własny kod QR, a bramka sprawdza limit godzinowy i duplikaty.</p>}
            {selected && (
              <>
                <div className="card">
                  <div className="row between">
                    <h2 style={{ margin: 0 }}>{selected.name}</h2>
                    <span className="soft">{selected.used} z {selected.capacity} miejsc · weszło {selected.entered}</span>
                  </div>
                  <form action={updateListAction} className="row" style={{ marginTop: 12 }}>
                    {hidden}<input type="hidden" name="listId" value={selected.id} />
                    <label style={{ margin: 0 }}>Limit</label><input name="capacity" type="number" min={1} defaultValue={selected.capacity} style={{ width: 90 }} />
                    <label style={{ margin: 0 }}>Wejście do</label><input name="entryUntil" type="datetime-local" defaultValue={toLocalInput(selected.entry_until)} style={{ width: 'auto' }} />
                    <button className="ghost small">Zapisz</button>
                  </form>
                </div>
                <form action={addGuestsAction} className="card">
                  {hidden}<input type="hidden" name="listId" value={selected.id} />
                  <h3>Dopisz gości</h3>
                  <div className="field">
                    <label>Imię i nazwisko — jedna osoba w wierszu, osoby towarzyszące jako „+2”</label>
                    <textarea name="guests" rows={4} placeholder={'Anna Nowak\nJan Kowalski +2'} required />
                  </div>
                  <div className="form-grid">
                    <div className="field"><label>Telefon (przy jednej osobie)</label><input name="phone" type="tel" /></div>
                    <div className="field"><label>E-mail (przy jednej osobie)</label><input name="email" type="email" /></div>
                  </div>
                  <button>Dodaj do listy</button>
                </form>
                <div className="card table-wrap">
                  <table>
                    <thead><tr><th>Gość</th><th className="num">Osób</th><th>Zaproszenie</th><th>Wejście</th><th /></tr></thead>
                    <tbody>
                      {entries.map((g) => (
                        <tr key={g.id} className={g.status === 'void' ? 'dim' : ''}>
                          <td>{g.full_name}<div className="muted">{g.phone}</div></td>
                          <td className="num">{1 + g.plus_ones}</td>
                          <td><a href={`${env.appUrl}/zaproszenie/${g.code}`} target="_blank" rel="noreferrer"><code>{g.code}</code></a></td>
                          <td>{g.checked_in_at ? <span className="tag ok">{fmtTime(g.checked_in_at)}</span> : <span className="muted">—</span>}</td>
                          <td>{g.status === 'invited' && !g.checked_in_at && (
                            <form action={voidGuestAction}>{hidden}<input type="hidden" name="listId" value={selected.id} /><input type="hidden" name="entryId" value={g.id} /><button className="danger small">Usuń</button></form>
                          )}</td>
                        </tr>
                      ))}
                      {entries.length === 0 && <tr><td colSpan={5} className="muted">Lista jest pusta.</td></tr>}
                    </tbody>
                  </table>
                </div>
              </>
            )}
          </section>
        </div>
      </main>
    </>
  );
}
