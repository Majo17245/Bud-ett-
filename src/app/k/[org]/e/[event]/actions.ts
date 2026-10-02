'use server';

import { cookies } from 'next/headers';
import { act, bool, int, optStr, str } from '@/lib/forms';
import { UserError } from '@/lib/db';
import { createLoungeReservation, createTicketOrder, type BuyerInput } from '@/lib/services/orders';

function buyer(fd: FormData): BuyerInput {
  return {
    name: str(fd, 'name'), email: str(fd, 'email'), phone: optStr(fd, 'phone'),
    lang: str(fd, 'lang') === 'en' ? 'en' : 'pl', marketingConsent: bool(fd, 'marketing'), termsAccepted: bool(fd, 'terms'),
  };
}

async function promoterCode(fd: FormData, orgSlug: string) {
  return optStr(fd, 'p') ?? (await cookies()).get(`ref_${orgSlug}`)?.value ?? null;
}

function back(fd: FormData, anchor: string) {
  const lang = str(fd, 'lang') === 'en' ? '?lang=en' : '';
  return `/k/${str(fd, 'orgSlug')}/e/${str(fd, 'eventSlug')}${lang}#${anchor}`;
}

export async function buyTicketsAction(fd: FormData) {
  await act(back(fd, 'bilety'), async () => {
    const items: { ticketTypeId: string; quantity: number }[] = [];
    for (const [k, v] of fd.entries()) {
      if (k.startsWith('qty_')) {
        const quantity = Number(v);
        if (Number.isInteger(quantity) && quantity > 0) items.push({ ticketTypeId: k.slice(4), quantity });
      }
    }
    const r = await createTicketOrder({
      eventId: str(fd, 'eventId'), items, buyer: buyer(fd), discountCode: optStr(fd, 'discount'),
      promoterCode: await promoterCode(fd, str(fd, 'orgSlug')),
    });
    return { to: r.redirectUrl };
  });
}

export async function reserveLoungeAction(fd: FormData) {
  await act(back(fd, 'loze'), async () => {
    const loungeId = str(fd, 'loungeId');
    if (!loungeId) throw new UserError('Wybierz lożę na mapie.');
    const r = await createLoungeReservation({
      eventId: str(fd, 'eventId'), loungeId, persons: int(fd, 'persons') ?? 0, buyer: buyer(fd),
      promoterCode: await promoterCode(fd, str(fd, 'orgSlug')), notes: optStr(fd, 'notes'),
    });
    return { to: r.redirectUrl };
  });
}
