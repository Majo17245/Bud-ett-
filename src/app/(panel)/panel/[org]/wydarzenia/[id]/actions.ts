'use server';

import { act, bool, date, int, money, optStr, str } from '@/lib/forms';
import { requireOrg, setSecretFlash } from '@/lib/session';
import { one, UserError } from '@/lib/db';
import { addTicketType, getEvent, setEventStatus, setTicketTypeActive, updateEvent, updateTicketTypeQuantity } from '@/lib/services/events';
import { addGuests, createList, parseGuestLine, updateList, voidGuest } from '@/lib/services/lists';
import { addManualReservation, setReservationStatus } from '@/lib/services/lounges';
import { createDoorToken, importExternalTickets, revokeDoorToken } from '@/lib/services/door';
import { createDiscountCode, setDiscountActive } from '@/lib/services/orgs';
import { env } from '@/lib/env';

/** Sprawdza uprawnienia i to, że impreza należy do klubu. */
async function ctx(fd: FormData, roles: ('owner' | 'manager' | 'door')[] = ['owner', 'manager']) {
  const { user, org } = await requireOrg(str(fd, 'org'), roles);
  const event = await getEvent(org.id, str(fd, 'event'));
  if (!event) throw new Error('Nie ma takiej imprezy w tym klubie');
  return { user, org, event, base: `/panel/${org.slug}/wydarzenia/${event.id}` };
}

export async function updateEventAction(fd: FormData) {
  const { org, event, base } = await ctx(fd);
  await act(base, async () => {
    await updateEvent(org.id, event.id, {
      name: str(fd, 'name'), startsAt: date(fd, 'startsAt'), endsAt: date(fd, 'endsAt'), venueName: optStr(fd, 'venueName'),
      description: str(fd, 'description'), capacity: int(fd, 'capacity'), minAge: int(fd, 'minAge'),
    });
    return 'Zapisano.';
  });
}

export async function setStatusAction(fd: FormData) {
  const { org, event, base } = await ctx(fd);
  await act(base, async () => {
    const status = str(fd, 'status');
    if (!['draft', 'published', 'cancelled'].includes(status)) throw new UserError('Nieznany status.');
    await setEventStatus(org.id, event.id, status as 'draft' | 'published' | 'cancelled');
    return status === 'published' ? 'Impreza opublikowana — sprzedaż ruszyła.' : status === 'cancelled' ? 'Impreza odwołana.' : 'Impreza ukryta.';
  });
}

export async function addTicketTypeAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(base, async () => {
    await addTicketType(event.id, {
      tierGroup: str(fd, 'tierGroup'), name: str(fd, 'name'), price: money(fd, 'price'), quantity: int(fd, 'quantity'),
      groupSize: int(fd, 'groupSize'), salesStart: date(fd, 'salesStart'), salesEnd: date(fd, 'salesEnd'),
    });
    return 'Dodano pulę biletów.';
  });
}

export async function ticketTypeAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(base, async () => {
    const id = str(fd, 'id');
    if (fd.has('quantity')) {
      const qty = int(fd, 'quantity');
      if (qty == null || qty < 0) throw new UserError('Podaj liczbę biletów.');
      await updateTicketTypeQuantity(event.id, id, qty);
      return 'Zmieniono wielkość puli.';
    }
    await setTicketTypeActive(event.id, id, bool(fd, 'active'));
  });
}

export async function discountAction(fd: FormData) {
  const { org, event, base } = await ctx(fd);
  await act(base, async () => {
    if (fd.has('id')) {
      await setDiscountActive(org.id, str(fd, 'id'), bool(fd, 'active'));
      return;
    }
    await createDiscountCode(org.id, event.id, { code: str(fd, 'code'), percentOff: int(fd, 'percentOff'), maxUses: int(fd, 'maxUses') });
    return 'Dodano kod rabatowy.';
  });
}

// ---------- Listy ----------

export async function createListAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(`${base}/listy`, async () => {
    await createList(event.id, { name: str(fd, 'name'), capacity: int(fd, 'capacity'), promoterId: optStr(fd, 'promoterId'), entryUntil: date(fd, 'entryUntil') });
    return 'Lista utworzona.';
  });
}

export async function updateListAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(`${base}/listy?lista=${str(fd, 'listId')}`, async () => {
    await updateList(event.id, str(fd, 'listId'), { capacity: int(fd, 'capacity'), entryUntil: date(fd, 'entryUntil') });
    return 'Zapisano listę.';
  });
}

export async function addGuestsAction(fd: FormData) {
  const { user, event, base } = await ctx(fd);
  const listId = str(fd, 'listId');
  await act(`${base}/listy?lista=${listId}`, async () => {
    const lines = str(fd, 'guests').split(/\r?\n/).map(parseGuestLine).filter((g): g is NonNullable<typeof g> => !!g);
    const phone = optStr(fd, 'phone');
    const email = optStr(fd, 'email');
    if (lines.length === 1) Object.assign(lines[0], { phone, email });
    const list = await one('select 1 from guest_lists where id = $1 and event_id = $2', [listId, event.id]);
    if (!list) throw new UserError('Nie ma takiej listy.');
    const added = await addGuests(listId, lines, `manager:${user.id}`);
    return added.length === 1 ? `Dodano: ${added[0].fullName}.` : `Dodano ${added.length} osób.`;
  });
}

export async function voidGuestAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(`${base}/listy?lista=${str(fd, 'listId')}`, async () => {
    await voidGuest(event.id, str(fd, 'entryId'));
    return 'Usunięto z listy.';
  });
}

// ---------- Loże ----------

export async function addReservationAction(fd: FormData) {
  const { org, event, base } = await ctx(fd);
  await act(`${base}/loze`, async () => {
    const source = str(fd, 'source');
    await addManualReservation(org.id, event.id, {
      loungeId: str(fd, 'loungeId'), name: str(fd, 'name'), phone: optStr(fd, 'phone'), persons: int(fd, 'persons') ?? 0,
      source: source === 'dm' ? 'dm' : source === 'phone' ? 'phone' : 'panel', notes: optStr(fd, 'notes'),
    });
    return 'Rezerwacja dodana.';
  });
}

export async function reservationStatusAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(`${base}/loze`, async () => {
    const status = str(fd, 'status');
    if (!['confirmed', 'cancelled', 'no_show'].includes(status)) throw new UserError('Nieznany status.');
    await setReservationStatus(event.id, str(fd, 'id'), status as 'confirmed' | 'cancelled' | 'no_show');
    return status === 'confirmed' ? 'Potwierdzono — zadzwoń lub napisz do gościa.' : 'Zapisano.';
  });
}

// ---------- Bramka ----------

export async function createDoorLinkAction(fd: FormData) {
  const { event, base } = await ctx(fd, ['owner', 'manager', 'door']);
  await act(`${base}/bramka`, async () => {
    const token = await createDoorToken(event.id, str(fd, 'label') || 'Bramka');
    await setSecretFlash('bramka', `${env.appUrl}/bramka/${event.id}#t=${token}`);
    return 'Link do skanera gotowy — zeskanuj kod QR telefonem bramki.';
  });
}

export async function revokeDoorLinkAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(`${base}/bramka`, async () => {
    await revokeDoorToken(event.id, str(fd, 'id'));
    return 'Link wyłączony.';
  });
}

export async function importExternalAction(fd: FormData) {
  const { event, base } = await ctx(fd);
  await act(`${base}/bramka`, async () => {
    const file = fd.get('file');
    let text = str(fd, 'codes');
    if (file instanceof File && file.size > 0) {
      if (file.size > 5_000_000) throw new UserError('Plik jest za duży (maks. 5 MB).');
      text = await file.text();
    }
    const r = await importExternalTickets(event.id, str(fd, 'source'), text);
    return `Wczytano ${r.added} kodów${r.skipped ? `, pominięto ${r.skipped} (już były)` : ''}.`;
  });
}
