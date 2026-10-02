import { Flash } from '@/components/Flash';
import { PanelNav } from '@/components/PanelNav';
import { readSecretFlash, requireOrg } from '@/lib/session';
import { teamMembers } from '@/lib/services/orgs';
import { PLANS, ADDONS } from '@/lib/pricing';
import { zl } from '@/lib/money';
import { env } from '@/lib/env';
import { addMemberAction, removeMemberAction, savePaymentsAction, saveProfileAction } from '../actions';

const ROLES: Record<string, string> = { owner: 'właściciel', manager: 'manager', door: 'bramka' };

export default async function SettingsPage({ params, searchParams }: { params: Promise<{ org: string }>; searchParams: Promise<{ ok?: string; blad?: string }> }) {
  const { org: slug } = await params;
  const sp = await searchParams;
  const { user, org } = await requireOrg(slug, ['owner']);
  const [team, secret] = await Promise.all([teamMembers(org.id), readSecretFlash()]);
  return (
    <>
      <PanelNav org={org} active="ustawienia" userName={user.name} />
      <main className="wrap">
        <h1>Ustawienia</h1>
        <Flash sp={sp} />
        {secret && <div className="flash info">{secret}</div>}
        <div className="grid grid-2">
          <form action={saveProfileAction} className="card">
            <input type="hidden" name="org" value={org.slug} />
            <h2>Klub</h2>
            <div className="field"><label>Nazwa</label><input name="name" defaultValue={org.name} required /></div>
            <div className="form-grid">
              <div className="field"><label>Miasto</label><input name="city" defaultValue={org.city ?? ''} /></div>
              <div className="field"><label>Pojemność sali</label><input name="capacity" type="number" min={1} defaultValue={org.capacity ?? ''} /></div>
            </div>
            <div className="field"><label>Adres</label><input name="address" defaultValue={org.address ?? ''} /></div>
            <div className="form-grid">
              <div className="field"><label>E-mail do powiadomień</label><input name="contactEmail" type="email" defaultValue={org.contact_email ?? ''} /></div>
              <div className="field"><label>Instagram</label><input name="instagram" defaultValue={org.instagram ?? ''} placeholder="nazwa_klubu" /></div>
            </div>
            <div className="form-grid">
              <div className="field">
                <label>Plan</label>
                <select name="plan" defaultValue={org.plan}>
                  {Object.entries(PLANS).map(([k, p]) => <option key={k} value={k}>{p.label} — {p.monthly ? zl(p.monthly) + '/mies.' : '0 zł'}</option>)}
                </select>
              </div>
              <div className="field">
                <label>Opłatę serwisową płaci</label>
                <select name="feePayer" defaultValue={org.fee_payer}>
                  <option value="buyer">kupujący (doliczana do ceny)</option>
                  <option value="org">klub (cena bez dopłat)</option>
                </select>
              </div>
            </div>
            <p className="muted" style={{ fontSize: '.85rem' }}>
              Opłaty planu {PLANS[org.plan].label}: bilety {PLANS[org.plan].ticketPct}% (min. {zl(PLANS[org.plan].minTicketFee)}), loże {PLANS[org.plan].loungePct}%. Zawierają koszty płatności.
            </p>
            <button type="submit">Zapisz</button>
          </form>

          <form action={savePaymentsAction} className="card">
            <input type="hidden" name="org" value={org.slug} />
            <h2>Płatności online</h2>
            <p className="soft" style={{ fontSize: '.9rem' }}>
              Pieniądze trafiają od razu na konto klubu u operatora — system nie przechowuje pieniędzy gości ani danych kart.
              Klub zakłada konto w Przelewy24 (weryfikacja trwa od kilku godzin do kilku dni) i wkleja tu dane z panelu operatora.
            </p>
            <div className="field">
              <label>Operator</label>
              <select name="provider" defaultValue={org.payment_provider}>
                <option value="none">brak — tylko listy, loże na prośbę, bramka</option>
                {env.allowMockPayments && <option value="mock">symulator płatności (testy)</option>}
                <option value="przelewy24">Przelewy24 (BLIK, karty, Apple Pay, Google Pay)</option>
              </select>
            </div>
            <div className="form-grid">
              <div className="field"><label>ID sprzedawcy (merchantId)</label><input name="merchantId" inputMode="numeric" defaultValue={org.p24_merchant_id ?? ''} /></div>
              <div className="field"><label>ID sklepu (posId)</label><input name="posId" inputMode="numeric" defaultValue={org.p24_pos_id ?? ''} /></div>
              <div className="field"><label>Klucz CRC</label><input name="crc" type="password" autoComplete="off" placeholder={org.p24_merchant_id ? '•••• zapisany' : ''} /></div>
              <div className="field"><label>Klucz API (do raportów)</label><input name="apiKey" type="password" autoComplete="off" placeholder={org.p24_merchant_id ? '•••• zapisany' : ''} /></div>
            </div>
            <label className="check field"><input type="checkbox" name="sandbox" defaultChecked={org.p24_sandbox} /> tryb testowy (sandbox Przelewy24)</label>
            <p className="muted" style={{ fontSize: '.85rem' }}>Adres powiadomień do wpisania w panelu P24: <code>{env.appUrl}/api/platnosci/p24</code></p>
            <button type="submit">Zapisz płatności</button>
          </form>
        </div>

        <div className="card">
          <h2>Zespół</h2>
          <div className="table-wrap">
            <table>
              <thead><tr><th>Osoba</th><th>E-mail</th><th>Rola</th><th /></tr></thead>
              <tbody>
                {team.map((m) => (
                  <tr key={m.user_id}>
                    <td>{m.name}</td><td>{m.email}</td><td>{ROLES[m.role]}</td>
                    <td>{m.user_id !== user.id && (
                      <form action={removeMemberAction}><input type="hidden" name="org" value={org.slug} /><input type="hidden" name="userId" value={m.user_id} /><button className="danger small">Usuń</button></form>
                    )}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <form action={addMemberAction} className="form-grid" style={{ marginTop: 16, alignItems: 'end' }}>
            <input type="hidden" name="org" value={org.slug} />
            <div className="field"><label>Imię i nazwisko</label><input name="name" /></div>
            <div className="field"><label>E-mail</label><input name="email" type="email" required /></div>
            <div className="field"><label>Rola</label><select name="role" defaultValue="manager"><option value="manager">manager</option><option value="door">bramka</option><option value="owner">właściciel</option></select></div>
            <div className="field"><button type="submit" className="block">Dodaj osobę</button></div>
          </form>
        </div>

        <div className="card">
          <h2>Dodatki</h2>
          <ul className="soft">
            <li>Wdrożenie na miejscu: {zl(ADDONS.onsiteSetup)} (gratis przy umowie rocznej)</li>
            <li>SMS ponad pakiet: {zl(ADDONS.smsOverPackage)}</li>
            <li>Zestaw na bramkę (telefon i drukarka): {zl(ADDONS.doorKitPerEvent)} za imprezę</li>
            <li>Projekt strony klubu: {zl(ADDONS.websiteDesign)}</li>
          </ul>
        </div>
      </main>
    </>
  );
}
