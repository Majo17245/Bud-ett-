import { notFound } from 'next/navigation';
import { requireOrg } from '@/lib/session';
import { getEvent } from '@/lib/services/events';
import { buildManifest } from '@/lib/services/door';
import { fmtDateTime, fmtTime } from '@/lib/time';

const KIND: Record<string, string> = { ticket: 'bilet', guest: 'lista', lounge: 'loża', external: 'inna platforma' };

export default async function PrintPage({ params }: { params: Promise<{ org: string; id: string }> }) {
  const { org: slug, id } = await params;
  const { org } = await requireOrg(slug, ['owner', 'manager', 'door']);
  const event = await getEvent(org.id, id);
  if (!event) notFound();
  const m = await buildManifest(event.id);
  const entries = (m?.entries ?? []).filter((e) => !e.v).sort((a, b) => a.n.localeCompare(b.n, 'pl'));
  return (
    <main className="wrap">
      <div className="no-print row between" style={{ marginBottom: 12 }}>
        <span className="soft">Lista na wypadek awarii — wydrukuj przed otwarciem drzwi (Ctrl+P).</span>
      </div>
      <h1>{event.name} — lista wejść</h1>
      <p>{fmtDateTime(event.starts_at)} · wygenerowano {fmtDateTime(new Date())} · {entries.length} pozycji · odhaczaj wejścia długopisem</p>
      <table>
        <thead><tr><th>✓</th><th>Nazwisko</th><th className="num">Osób</th><th>Rodzaj</th><th>Kod</th><th>Uwagi</th></tr></thead>
        <tbody>
          {entries.map((e) => (
            <tr key={e.c}>
              <td>{e.x ? '✔' : '☐'}</td><td>{e.n || '—'}</td><td className="num">{e.p}</td><td>{KIND[e.k]} · {e.i}</td>
              <td className="mono">{e.c}</td><td>{e.u ? `wejście do ${fmtTime(e.u)}` : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
