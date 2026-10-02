import Link from 'next/link';
import { redirect } from 'next/navigation';
import { Flash } from '@/components/Flash';
import { PanelNav } from '@/components/PanelNav';
import { requireUser } from '@/lib/session';
import { membershipsFor } from '@/lib/services/users';
import { createOrgAction } from '../actions';

export const metadata = { title: 'Panel' };

export default async function PanelHome({ searchParams }: { searchParams: Promise<{ ok?: string; blad?: string; nowy?: string }> }) {
  const user = await requireUser();
  const sp = await searchParams;
  const orgs = await membershipsFor(user.id);
  if (orgs.length === 1 && !sp.nowy && !sp.blad) redirect(`/panel/${orgs[0].slug}`);
  return (
    <>
      <PanelNav userName={user.name} />
      <main className="wrap">
        <h1>Twoje kluby</h1>
        <Flash sp={sp} />
        <div className="grid grid-3">
          {orgs.map((o) => (
            <Link key={o.id} href={`/panel/${o.slug}`} className="event-card">
              <strong>{o.name}</strong>
              <div className="muted">{o.city ?? '—'} · rola: {o.role}</div>
            </Link>
          ))}
        </div>
        <form action={createOrgAction} className="card" style={{ marginTop: 24, maxWidth: 520 }}>
          <h2>Dodaj klub lub organizatora</h2>
          <div className="field"><label htmlFor="orgName">Nazwa</label><input id="orgName" name="orgName" required /></div>
          <div className="form-grid">
            <div className="field"><label htmlFor="kind">Rodzaj</label><select id="kind" name="kind"><option value="club">Klub</option><option value="organizer">Organizator</option></select></div>
            <div className="field"><label htmlFor="city">Miasto</label><input id="city" name="city" /></div>
          </div>
          <button type="submit">Dodaj</button>
        </form>
      </main>
    </>
  );
}
