import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Flash } from '@/components/Flash';
import { EventTabs, PanelNav } from '@/components/PanelNav';
import { Qr } from '@/components/Qr';
import { readSecretFlash, requireOrg } from '@/lib/session';
import { getEvent } from '@/lib/services/events';
import { doorSummary, doorTokens, externalTicketCounts } from '@/lib/services/door';
import { fmtDateTime } from '@/lib/time';
import { createDoorLinkAction, importExternalAction, revokeDoorLinkAction } from '../actions';

export default async function DoorAdminPage({ params, searchParams }: { params: Promise<{ org: string; id: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { org: slug, id } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug, ['owner', 'manager', 'door']);
  const event = await getEvent(org.id, id);
  if (!event) notFound();
  const [tokens, external, summary, secret] = await Promise.all([doorTokens(event.id), externalTicketCounts(event.id), doorSummary(event.id), readSecretFlash()]);
  const doorLink = secret?.includes(`/bramka/${event.id}#t=`) ? secret : null;
  const hidden = (<><input type="hidden" name="org" value={org.slug} /><input type="hidden" name="event" value={event.id} /></>);
  const isManager = org.role !== 'door';

  return (
    <>
      <PanelNav org={org} active="wydarzenia" userName={user.name} />
      <main className="wrap">
        <h1>{event.name}</h1>
        {isManager && <EventTabs orgSlug={org.slug} eventId={event.id} active="bramka" />}
        <Flash sp={sp} />
        <div className="stats">
          <div className="stat"><b>{summary.inside}</b><span>w sali teraz</span></div>
          <div className="stat"><b>{summary.entered}</b><span>weszło łącznie</span></div>
          <div className="stat"><b>{summary.scans}</b><span>skanów</span></div>
        </div>
        <div className="grid grid-2">
          <div className="card">
            <h2>Telefony bramki</h2>
            <p className="soft">Każdy telefon ochrony dostaje własny link — bez zakładania kont. Otwórz go z internetem przed imprezą: skaner pobierze listę kodów i dalej działa także bez zasięgu.</p>
            {doorLink && (
              <div className="qr-ticket" style={{ maxWidth: 320 }}>
                <Qr value={doorLink} label="Kod QR z linkiem do skanera" />
                <div style={{ fontSize: '.8rem', wordBreak: 'break-all', marginTop: 8 }}>{doorLink}</div>
                <div style={{ fontSize: '.8rem', marginTop: 4 }}>Zeskanuj aparatem telefonu bramki. Kod zniknie za 2 minuty.</div>
              </div>
            )}
            <form action={createDoorLinkAction} className="row">
              {hidden}
              <input name="label" placeholder="np. Wejście główne, telefon 1" style={{ flex: 1, minWidth: 180 }} />
              <button>Nowy link do skanera</button>
            </form>
            <table style={{ marginTop: 12 }}>
              <tbody>
                {tokens.map((t) => (
                  <tr key={t.id} className={t.revoked_at ? 'dim' : ''}>
                    <td>{t.label}</td><td className="muted">ważny do {fmtDateTime(t.expires_at)}</td>
                    <td>{!t.revoked_at && isManager && <form action={revokeDoorLinkAction}>{hidden}<input type="hidden" name="id" value={t.id} /><button className="danger small">Wyłącz</button></form>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p style={{ marginTop: 12 }}><Link className="btn ghost" href={`/bramka/${event.id}`}>Otwórz skaner na tym urządzeniu</Link></p>
          </div>

          <div className="card">
            <h2>Plan B: lista do druku</h2>
            <p className="soft">Na wypadek awarii telefonu lub prądu: wydrukuj alfabetyczną listę wszystkich biletów, gości z list i loż z kodami.</p>
            <Link className="btn ghost" href={`/panel/${org.slug}/wydarzenia/${event.id}/druk`} target="_blank">Lista do druku</Link>
            {isManager && (
              <>
                <hr />
                <h2>Bilety z innych platform</h2>
                <p className="soft">Jedna bramka dla wszystkich kanałów: wgraj eksport kodów z RA, Going, Biletomatu lub eBilet. Format: kod;imię i nazwisko;rodzaj biletu (dwie ostatnie kolumny opcjonalne).</p>
                {external.length > 0 && (
                  <ul>{external.map((x) => <li key={x.source}><strong>{x.source.toUpperCase()}</strong>: {x.total} kodów, weszło {x.entered}</li>)}</ul>
                )}
                <form action={importExternalAction}>
                  {hidden}
                  <div className="form-grid">
                    <div className="field"><label>Źródło</label><select name="source"><option value="ra">Resident Advisor</option><option value="going">Going</option><option value="biletomat">Biletomat</option><option value="ebilet">eBilet</option><option value="other">inne</option></select></div>
                    <div className="field"><label>Plik CSV</label><input name="file" type="file" accept=".csv,.txt,text/csv,text/plain" /></div>
                  </div>
                  <div className="field"><label>…albo wklej kody</label><textarea name="codes" rows={4} placeholder={'RA-123456;Jan Kowalski;Early bird\nRA-123457'} /></div>
                  <button>Wczytaj kody</button>
                </form>
              </>
            )}
          </div>
        </div>
      </main>
    </>
  );
}
