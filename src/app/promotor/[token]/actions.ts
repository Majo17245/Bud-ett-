'use server';

import { act, optStr, str } from '@/lib/forms';
import { UserError } from '@/lib/db';
import { addGuests, parseGuestLine, voidGuest } from '@/lib/services/lists';
import { promoterByToken } from '@/lib/services/promoters';

async function promoter(fd: FormData) {
  const p = await promoterByToken(str(fd, 'token'));
  if (!p) throw new UserError('Link wygasł — poproś managera o nowy.');
  return p;
}

export async function promoterAddGuestsAction(fd: FormData) {
  await act(`/promotor/${str(fd, 'token')}#lista-${str(fd, 'listId')}`, async () => {
    const p = await promoter(fd);
    const lines = str(fd, 'guests').split(/\r?\n/).map(parseGuestLine).filter((g): g is NonNullable<typeof g> => !!g);
    if (lines.length === 1) Object.assign(lines[0], { phone: optStr(fd, 'phone') });
    const added = await addGuests(str(fd, 'listId'), lines, `promoter:${p.id}`, { promoterId: p.id });
    return added.length === 1 ? `Dodano: ${added[0].fullName}. Wyślij gościowi link do zaproszenia.` : `Dodano ${added.length} osób.`;
  });
}

export async function promoterVoidGuestAction(fd: FormData) {
  await act(`/promotor/${str(fd, 'token')}`, async () => {
    const p = await promoter(fd);
    await voidGuest(str(fd, 'eventId'), str(fd, 'entryId'), { promoterId: p.id });
    return 'Usunięto z listy.';
  });
}
