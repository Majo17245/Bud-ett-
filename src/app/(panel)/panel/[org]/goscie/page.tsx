import { Flash } from '@/components/Flash';
import { PanelNav } from '@/components/PanelNav';
import { requireOrg } from '@/lib/session';
import { guestStats, listGuests } from '@/lib/services/guests';
import { zl } from '@/lib/money';
import { fmtDateTime } from '@/lib/time';
import { anonymizeGuestAction } from '../actions';

export default async function GuestsPage({ params, searchParams }: { params: Promise<{ org: string }>; searchParams: Promise<{ ok?: string; blad?: string; q?: string; zgoda?: string }> }) {
  const { org: slug } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug);
  const [guests, stats] = await Promise.all([listGuests(org.id, { search: sp.q, consentOnly: sp.zgoda === '1' }), guestStats(org.id)]);
  return (
    <>
      <PanelNav org={org} active="goscie" userName={user.name} />
      <main className="wrap">
        <h1>Baza gości</h1>
        <p className="soft">Goście trafiają tu z zakupów, rezerwacji loż i list. Do kampanii używaj tylko osób ze zgodą marketingową. Dane przetwarzamy w imieniu klubu (umowa powierzenia).</p>
        <Flash sp={sp} />
        <div className="stats">
          <div className="stat"><b>{stats?.total ?? 0}</b><span>gości w bazie</span></div>
          <div className="stat"><b>{stats?.consent ?? 0}</b><span>ze zgodą marketingową</span></div>
        </div>
        <form className="row card" method="get">
          <input name="q" defaultValue={sp.q} placeholder="Szukaj: imię, e-mail, telefon" style={{ flex: 1, minWidth: 200 }} />
          <label className="check" style={{ margin: 0 }}><input type="checkbox" name="zgoda" value="1" defaultChecked={sp.zgoda === '1'} /> tylko ze zgodą</label>
          <button type="submit" className="ghost">Filtruj</button>
          <a className="btn ghost" href={`/panel/${org.slug}/goscie/csv`}>Eksport CSV (zgody)</a>
        </form>
        <div className="card table-wrap">
          <table>
            <thead><tr><th>Gość</th><th>Kontakt</th><th>Zgoda</th><th className="num">Zamówienia</th><th className="num">Wydał</th><th>Ostatnio</th><th /></tr></thead>
            <tbody>
              {guests.map((g) => (
                <tr key={g.id}>
                  <td>{g.name ?? '—'}</td>
                  <td>{g.email}<div className="muted">{g.phone}</div></td>
                  <td>{g.marketing_consent ? <span className="tag ok">tak</span> : <span className="tag">nie</span>}</td>
                  <td className="num">{g.orders_count}</td><td className="num">{zl(g.total_spent)}</td>
                  <td>{fmtDateTime(g.last_seen_at)}</td>
                  <td>
                    <form action={anonymizeGuestAction}>
                      <input type="hidden" name="org" value={org.slug} /><input type="hidden" name="id" value={g.id} />
                      <button className="danger small" title="Prawo do usunięcia danych (RODO)">Usuń dane</button>
                    </form>
                  </td>
                </tr>
              ))}
              {guests.length === 0 && <tr><td colSpan={7} className="muted">Brak gości.</td></tr>}
            </tbody>
          </table>
        </div>
      </main>
    </>
  );
}
