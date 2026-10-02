import Link from 'next/link';
import { Flash } from '@/components/Flash';
import { PanelNav } from '@/components/PanelNav';
import { requireOrg } from '@/lib/session';
import { listEvents } from '@/lib/services/events';
import { fmtDateTime, nextWeekdayAt, toLocalInput } from '@/lib/time';
import { PLANS } from '@/lib/pricing';
import { createEventAction } from './actions';

const STATUS: Record<string, [string, string]> = { draft: ['szkic', ''], published: ['w sprzedaży', 'ok'], cancelled: ['odwołana', 'bad'] };

export default async function OrgHome({ params, searchParams }: { params: Promise<{ org: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { org: slug } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug, ['owner', 'manager', 'door']);
  const events = await listEvents(org.id);
  const now = Date.now();
  const upcoming = events.filter((e) => new Date(e.ends_at).getTime() > now).reverse();
  const past = events.filter((e) => new Date(e.ends_at).getTime() <= now);
  const nextFriday = nextWeekdayAt(5, 22);
  const isDoor = org.role === 'door';

  return (
    <>
      <PanelNav org={org} active="wydarzenia" userName={user.name} />
      <main className="wrap">
        <div className="row between">
          <h1>Imprezy</h1>
          <span className="tag accent">Plan {PLANS[org.plan].label}</span>
        </div>
        <Flash sp={sp} />
        {org.payment_provider === 'none' && !isDoor && (
          <div className="flash info">
            Płatności online są wyłączone — możesz prowadzić listy gości, loże na prośbę i bramkę (tryb nocy testowej).
            Włącz Przelewy24 w <Link href={`/panel/${org.slug}/ustawienia`}>ustawieniach</Link>, gdy klub założy konto u operatora.
          </div>
        )}
        <h2>Nadchodzące</h2>
        {upcoming.length === 0 && <p className="soft">Brak nadchodzących imprez.</p>}
        <div className="grid grid-2">
          {upcoming.map((e) => (
            <Link key={e.id} href={isDoor ? `/panel/${org.slug}/wydarzenia/${e.id}/bramka` : `/panel/${org.slug}/wydarzenia/${e.id}`} className="event-card">
              <div className="row between">
                <span className="event-date">{fmtDateTime(e.starts_at)}</span>
                <span className={`tag ${STATUS[e.status][1]}`}>{STATUS[e.status][0]}</span>
              </div>
              <h3 style={{ margin: '6px 0' }}>{e.name}</h3>
              <div className="muted">Bilety: {e.tickets_sold} · na listach: {e.guests} · weszło: {e.entered}</div>
            </Link>
          ))}
        </div>

        {!isDoor && (
          <form action={createEventAction} className="card" style={{ marginTop: 24 }}>
            <input type="hidden" name="org" value={org.slug} />
            <h2>Nowa impreza</h2>
            <div className="form-grid">
              <div className="field" style={{ gridColumn: '1 / -1' }}><label htmlFor="name">Nazwa</label><input id="name" name="name" placeholder="np. Friday Night: R&B vs Hip-Hop" required /></div>
              <div className="field"><label htmlFor="startsAt">Początek</label><input id="startsAt" name="startsAt" type="datetime-local" defaultValue={toLocalInput(nextFriday)} required /></div>
              <div className="field"><label htmlFor="endsAt">Koniec</label><input id="endsAt" name="endsAt" type="datetime-local" defaultValue={toLocalInput(new Date(nextFriday.getTime() + 7 * 3600_000))} required /></div>
              <div className="field"><label htmlFor="capacity">Limit osób w sali</label><input id="capacity" name="capacity" type="number" min={1} defaultValue={org.capacity ?? undefined} /></div>
              <div className="field"><label htmlFor="minAge">Wiek</label><select id="minAge" name="minAge" defaultValue="18"><option value="">bez limitu</option><option value="16">16+</option><option value="18">18+</option><option value="21">21+</option></select></div>
              <div className="field"><label htmlFor="venueName">Miejsce (dla organizatorów)</label><input id="venueName" name="venueName" placeholder="np. Progresja" /></div>
              <div className="field" style={{ gridColumn: '1 / -1' }}><label htmlFor="description">Opis</label><textarea id="description" name="description" rows={3} /></div>
            </div>
            <button type="submit">Utwórz imprezę</button>
          </form>
        )}

        {past.length > 0 && (
          <>
            <h2 style={{ marginTop: 32 }}>Minione</h2>
            <div className="table-wrap card">
              <table>
                <thead><tr><th>Data</th><th>Impreza</th><th className="num">Bilety</th><th className="num">Na listach</th><th className="num">Weszło</th><th /></tr></thead>
                <tbody>
                  {past.map((e) => (
                    <tr key={e.id}>
                      <td>{fmtDateTime(e.starts_at)}</td><td>{e.name}</td>
                      <td className="num">{e.tickets_sold}</td><td className="num">{e.guests}</td><td className="num">{e.entered}</td>
                      <td><Link href={`/panel/${org.slug}/wydarzenia/${e.id}/raport`}>raport</Link></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>
    </>
  );
}
