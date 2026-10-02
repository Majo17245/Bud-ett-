'use server';

import { act, bool, date, int, money, num, optStr, str } from '@/lib/forms';
import { requireOrg, setSecretFlash } from '@/lib/session';
import { UserError } from '@/lib/db';
import { createEvent } from '@/lib/services/events';
import { createLounge, setLoungeActive, updateLounge, type LoungeInput } from '@/lib/services/lounges';
import { createPromoter, regeneratePanelToken, setPromoterActive } from '@/lib/services/promoters';
import { removeMember, updateOrgProfile, updatePayments } from '@/lib/services/orgs';
import { addMember } from '@/lib/services/users';
import { anonymizeGuest } from '@/lib/services/guests';
import { env } from '@/lib/env';

export async function createEventAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'));
  await act(`/panel/${org.slug}`, async () => {
    const ev = await createEvent(org.id, {
      name: str(fd, 'name'), startsAt: date(fd, 'startsAt'), endsAt: date(fd, 'endsAt'), venueName: optStr(fd, 'venueName'),
      description: str(fd, 'description'), capacity: int(fd, 'capacity'), minAge: int(fd, 'minAge'),
    });
    return { to: `/panel/${org.slug}/wydarzenia/${ev.id}`, ok: 'Impreza utworzona. Dodaj pule biletów i opublikuj.' };
  });
}

function loungeInput(fd: FormData): LoungeInput {
  return {
    name: str(fd, 'name'), zone: str(fd, 'zone'), capacity: int(fd, 'capacity'), maxCapacity: int(fd, 'maxCapacity'),
    basePrice: money(fd, 'basePrice'), extraPersonPrice: money(fd, 'extraPersonPrice'), minSpend: money(fd, 'minSpend'),
    prepayPercent: int(fd, 'prepayPercent'), mapX: num(fd, 'mapX'), mapY: num(fd, 'mapY'), mapW: num(fd, 'mapW'), mapH: num(fd, 'mapH'),
  };
}

export async function saveLoungeAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'));
  await act(`/panel/${org.slug}/loze`, async () => {
    const id = str(fd, 'id');
    if (id) await updateLounge(org.id, id, loungeInput(fd));
    else await createLounge(org.id, loungeInput(fd));
    return id ? 'Zapisano lożę.' : 'Dodano lożę.';
  });
}

export async function toggleLoungeAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'));
  await act(`/panel/${org.slug}/loze`, async () => {
    await setLoungeActive(org.id, str(fd, 'id'), bool(fd, 'active'));
  });
}

export async function createPromoterAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'));
  await act(`/panel/${org.slug}/promotorzy`, async () => {
    const p = await createPromoter(org.id, {
      name: str(fd, 'name'), code: str(fd, 'code'), phone: optStr(fd, 'phone'), email: optStr(fd, 'email'),
      ticketCommissionPct: num(fd, 'ticketCommissionPct'), guestCommission: money(fd, 'guestCommission'),
    });
    await setSecretFlash(`Prywatny link do panelu promotora ${p.code} (wyślij tylko jemu — działa bez hasła): ${env.appUrl}/promotor/${p.panelToken}`);
    return `Dodano promotora ${p.code}.`;
  });
}

export async function promoterLinkAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'));
  await act(`/panel/${org.slug}/promotorzy`, async () => {
    const token = await regeneratePanelToken(org.id, str(fd, 'id'));
    await setSecretFlash(`Nowy link do panelu promotora ${str(fd, 'code')}: ${env.appUrl}/promotor/${token}`);
    return 'Nowy link wygenerowany — poprzedni przestał działać.';
  });
}

export async function togglePromoterAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'));
  await act(`/panel/${org.slug}/promotorzy`, async () => {
    await setPromoterActive(org.id, str(fd, 'id'), bool(fd, 'active'));
  });
}

export async function saveProfileAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'), ['owner']);
  await act(`/panel/${org.slug}/ustawienia`, async () => {
    const plan = str(fd, 'plan');
    await updateOrgProfile(org.id, {
      name: str(fd, 'name'), city: optStr(fd, 'city'), address: optStr(fd, 'address'), capacity: int(fd, 'capacity'),
      contactEmail: optStr(fd, 'contactEmail'), instagram: optStr(fd, 'instagram'),
      feePayer: str(fd, 'feePayer') === 'org' ? 'org' : 'buyer',
      plan: plan === 'klub' || plan === 'premium' ? plan : 'start',
    });
    return 'Zapisano.';
  });
}

export async function savePaymentsAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'), ['owner']);
  await act(`/panel/${org.slug}/ustawienia`, async () => {
    const provider = str(fd, 'provider');
    if (!['none', 'mock', 'przelewy24'].includes(provider)) throw new UserError('Nieznany operator płatności.');
    await updatePayments(org.id, {
      provider: provider as 'none' | 'mock' | 'przelewy24', merchantId: int(fd, 'merchantId'), posId: int(fd, 'posId'),
      crc: optStr(fd, 'crc'), apiKey: optStr(fd, 'apiKey'), sandbox: bool(fd, 'sandbox'),
    });
    return 'Zapisano ustawienia płatności.';
  });
}

export async function addMemberAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'), ['owner']);
  await act(`/panel/${org.slug}/ustawienia`, async () => {
    const role = str(fd, 'role');
    if (!['owner', 'manager', 'door'].includes(role)) throw new UserError('Nieznana rola.');
    const { user, tempPassword } = await addMember(org.id, str(fd, 'email'), str(fd, 'name'), role as 'owner' | 'manager' | 'door');
    if (tempPassword) await setSecretFlash(`Hasło tymczasowe dla ${user.email}: ${tempPassword} — przekaż je osobiście, zniknie za 2 minuty.`);
    return `Dodano ${user.email} do zespołu.`;
  });
}

export async function removeMemberAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'), ['owner']);
  await act(`/panel/${org.slug}/ustawienia`, async () => {
    await removeMember(org.id, str(fd, 'userId'));
    return 'Usunięto z zespołu.';
  });
}

export async function anonymizeGuestAction(fd: FormData) {
  const { org } = await requireOrg(str(fd, 'org'));
  await act(`/panel/${org.slug}/goscie`, async () => {
    await anonymizeGuest(org.id, str(fd, 'id'));
    return 'Dane gościa usunięte (zostały tylko anonimowe statystyki).';
  });
}
