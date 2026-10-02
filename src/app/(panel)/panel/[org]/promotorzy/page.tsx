import { Flash } from '@/components/Flash';
import { PanelNav } from '@/components/PanelNav';
import { readSecretFlash, requireOrg } from '@/lib/session';
import { promoterStats, promotersForOrg } from '@/lib/services/promoters';
import { zl } from '@/lib/money';
import { createPromoterAction, promoterLinkAction, togglePromoterAction } from '../actions';

export default async function PromotersPage({ params, searchParams }: { params: Promise<{ org: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { org: slug } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug);
  const [promoters, stats] = await Promise.all([promotersForOrg(org.id), promoterStats(org.id)]);
  const secret = await readSecretFlash();
  const byId = new Map(stats.map((s) => [s.promoter_id, s]));
  return (
    <>
      <PanelNav org={org} active="promotorzy" userName={user.name} />
      <main className="wrap">
        <h1>Promotorzy i ambasadorzy</h1>
        <p className="soft">Każdy promotor ma własny kod do linków sprzedażowych, swoje listy z limitem i podgląd wyników na żywo. Prowizja liczy się sama: procent od biletów z jego linku + stała kwota za każdego gościa z jego listy, który wszedł.</p>
        <Flash sp={sp} />
        {secret && <div className="flash info" style={{ wordBreak: 'break-all' }}>{secret}</div>}
        <div className="card table-wrap">
          <h2>Ranking (wszystkie imprezy)</h2>
          <table>
            <thead><tr><th>#</th><th>Promotor</th><th>Kod</th><th className="num">Bilety</th><th className="num">Przychód z biletów</th><th className="num">Na listach</th><th className="num">Weszło z list</th><th className="num">Loże</th><th className="num">Prowizja</th><th /></tr></thead>
            <tbody>
              {promoters.map((p, i) => {
                const s = byId.get(p.id);
                return (
                  <tr key={p.id} className={p.active ? '' : 'dim'}>
                    <td>{i + 1}</td>
                    <td>{p.name}<div className="muted">{p.ticket_commission_pct}% + {zl(p.guest_commission)}/gość</div></td>
                    <td><code>{p.code}</code></td>
                    <td className="num">{s?.tickets ?? 0}</td><td className="num">{zl(s?.ticket_revenue ?? 0)}</td>
                    <td className="num">{s?.guests_listed ?? 0}</td><td className="num">{s?.guests_entered ?? 0}</td><td className="num">{s?.lounges ?? 0}</td>
                    <td className="num"><strong>{zl(s?.commission ?? 0)}</strong></td>
                    <td>
                      <div className="row" style={{ flexWrap: 'nowrap' }}>
                        <form action={promoterLinkAction}><input type="hidden" name="org" value={org.slug} /><input type="hidden" name="id" value={p.id} /><input type="hidden" name="code" value={p.code} /><button className="ghost small">Nowy link</button></form>
                        <form action={togglePromoterAction}><input type="hidden" name="org" value={org.slug} /><input type="hidden" name="id" value={p.id} /><input type="hidden" name="active" value={p.active ? '0' : '1'} /><button className="ghost small">{p.active ? 'Wyłącz' : 'Włącz'}</button></form>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {promoters.length === 0 && <tr><td colSpan={10} className="muted">Brak promotorów.</td></tr>}
            </tbody>
          </table>
        </div>
        <form action={createPromoterAction} className="card" style={{ maxWidth: 640 }}>
          <input type="hidden" name="org" value={org.slug} />
          <h2>Dodaj promotora</h2>
          <div className="form-grid">
            <div className="field"><label>Imię / ksywka</label><input name="name" required /></div>
            <div className="field"><label>Kod (opcjonalnie)</label><input name="code" placeholder="np. KAMIL" /></div>
            <div className="field"><label>Telefon</label><input name="phone" type="tel" /></div>
            <div className="field"><label>E-mail</label><input name="email" type="email" /></div>
            <div className="field"><label>Prowizja od biletów (%)</label><input name="ticketCommissionPct" inputMode="decimal" defaultValue="10" /></div>
            <div className="field"><label>Za gościa z listy (zł)</label><input name="guestCommission" inputMode="decimal" defaultValue="3" /></div>
          </div>
          <button type="submit">Dodaj promotora</button>
        </form>
      </main>
    </>
  );
}
