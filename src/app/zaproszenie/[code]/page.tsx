import { notFound } from 'next/navigation';
import { Qr } from '@/components/Qr';
import { guestByCode } from '@/lib/services/lists';
import { fmtDate, fmtTime } from '@/lib/time';

export const metadata = { title: 'Zaproszenie', robots: { index: false } };

export default async function InvitePage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const g = await guestByCode(code.toUpperCase());
  if (!g || g.status === 'void') notFound();
  return (
    <main className="narrow">
      <span className="brand">{g.org_name}</span>
      <h1 style={{ marginTop: 16 }}>Zaproszenie: {g.event_name}</h1>
      <p className="soft">{fmtDate(g.starts_at)} · {fmtTime(g.starts_at)} · {g.venue_name ?? g.org_name}{g.address ? `, ${g.address}` : ''}{g.min_age ? ` · ${g.min_age}+` : ''}</p>
      <div className={`qr-ticket ${g.checked_in_at ? 'used' : ''}`}>
        <div style={{ fontWeight: 700 }}>{g.full_name}{g.plus_ones ? ` +${g.plus_ones}` : ''}</div>
        <div style={{ fontSize: '.85rem', marginBottom: 8 }}>Lista: {g.list_name}</div>
        <Qr value={g.code} />
        <div className="code">{g.code}</div>
        {g.checked_in_at && <div>wykorzystane</div>}
      </div>
      {g.entry_until && <div className="flash info">Wejście z listy do godz. <strong>{fmtTime(g.entry_until)}</strong>. Później obowiązuje bilet.</div>}
      <p className="muted">Pokaż ten kod QR na bramce. {g.min_age ? 'Weź ze sobą dokument lub mObywatela.' : ''}</p>
    </main>
  );
}
