import { Flash } from '@/components/Flash';
import { PanelNav } from '@/components/PanelNav';
import { requireOrg } from '@/lib/session';
import { loungesForOrg, type Lounge } from '@/lib/services/lounges';
import { zl } from '@/lib/money';
import { saveLoungeAction, toggleLoungeAction } from '../actions';

const pln = (g: number) => (g / 100).toFixed(2).replace('.00', '');

function LoungeForm({ org, l }: { org: string; l?: Lounge }) {
  return (
    <form action={saveLoungeAction}>
      <input type="hidden" name="org" value={org} />
      {l && <input type="hidden" name="id" value={l.id} />}
      <div className="form-grid">
        <div className="field"><label>Nazwa</label><input name="name" defaultValue={l?.name} placeholder="Loża 1" required /></div>
        <div className="field"><label>Strefa</label><input name="zone" defaultValue={l?.zone ?? 'Sala główna'} /></div>
        <div className="field"><label>Osób w cenie</label><input name="capacity" type="number" min={1} defaultValue={l?.capacity ?? 6} required /></div>
        <div className="field"><label>Maks. osób</label><input name="maxCapacity" type="number" min={1} defaultValue={l?.max_capacity ?? 8} required /></div>
        <div className="field"><label>Cena loży (zł)</label><input name="basePrice" inputMode="decimal" defaultValue={l ? pln(l.base_price) : '600'} required /></div>
        <div className="field"><label>Dopłata za osobę (zł)</label><input name="extraPersonPrice" inputMode="decimal" defaultValue={l ? pln(l.extra_person_price) : '80'} /></div>
        <div className="field"><label>Minimalny wydatek (zł)</label><input name="minSpend" inputMode="decimal" defaultValue={l ? pln(l.min_spend) : '600'} /></div>
        <div className="field"><label>Przedpłata online (%)</label><input name="prepayPercent" type="number" min={0} max={100} defaultValue={l?.prepay_percent ?? 50} /></div>
        <div className="field"><label>Mapa: X / Y (%)</label><div className="row" style={{ flexWrap: 'nowrap' }}><input name="mapX" defaultValue={l?.map_x ?? 10} /><input name="mapY" defaultValue={l?.map_y ?? 20} /></div></div>
        <div className="field"><label>Mapa: szer. / wys. (%)</label><div className="row" style={{ flexWrap: 'nowrap' }}><input name="mapW" defaultValue={l?.map_w ?? 14} /><input name="mapH" defaultValue={l?.map_h ?? 14} /></div></div>
      </div>
      <button type="submit" className={l ? 'ghost small' : ''}>{l ? 'Zapisz' : 'Dodaj lożę'}</button>
    </form>
  );
}

export default async function LoungesPage({ params, searchParams }: { params: Promise<{ org: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { org: slug } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug);
  const lounges = await loungesForOrg(org.id);
  return (
    <>
      <PanelNav org={org} active="loze" userName={user.name} />
      <main className="wrap">
        <h1>Loże i mapa sali</h1>
        <p className="soft">Loże są wspólne dla wszystkich imprez klubu. Goście wybierają je na mapie i płacą przedpłatę online albo wysyłają prośbę o rezerwację.</p>
        <Flash sp={sp} />
        <div className="grid grid-2">
          <div className="card">
            <h2>Podgląd mapy</h2>
            <div className="floor" aria-label="Mapa sali">
              <div className="stage">scena / DJ</div>
              <div className="bar-area">bar</div>
              {lounges.filter((l) => l.active).map((l) => (
                <div key={l.id} className="spot" style={{ left: `${l.map_x}%`, top: `${l.map_y}%`, width: `${l.map_w}%`, height: `${l.map_h}%` }}>
                  <strong>{l.name}</strong><span>{zl(l.base_price)}</span>
                </div>
              ))}
            </div>
            <p className="muted" style={{ marginTop: 8 }}>Położenie ustawiasz w procentach szerokości i wysokości sali.</p>
          </div>
          <div className="card">
            <h2>Nowa loża</h2>
            <LoungeForm org={org.slug} />
          </div>
        </div>
        {lounges.map((l) => (
          <details key={l.id} className="card">
            <summary className="row between" style={{ cursor: 'pointer' }}>
              <span><strong>{l.name}</strong> <span className="muted">· {l.zone} · {l.capacity}–{l.max_capacity} os. · {zl(l.base_price)} · przedpłata {l.prepay_percent}%</span></span>
              {!l.active && <span className="tag">ukryta</span>}
            </summary>
            <div style={{ marginTop: 12 }}>
              <LoungeForm org={org.slug} l={l} />
              <form action={toggleLoungeAction} style={{ marginTop: 8 }}>
                <input type="hidden" name="org" value={org.slug} /><input type="hidden" name="id" value={l.id} />
                <input type="hidden" name="active" value={l.active ? '0' : '1'} />
                <button className="ghost small" type="submit">{l.active ? 'Ukryj lożę' : 'Przywróć lożę'}</button>
              </form>
            </div>
          </details>
        ))}
      </main>
    </>
  );
}
