export type Lang = 'pl' | 'en';

export const t = {
  pl: {
    events: 'Nadchodzące imprezy', noEvents: 'Brak zaplanowanych imprez — zajrzyj wkrótce.', tickets: 'Bilety', buy: 'Kupuję',
    soldOut: 'wyprzedane', ended: 'sprzedaż zakończona', upcoming: 'wkrótce', waiting: 'po wyprzedaniu poprzedniej puli',
    fee: 'opłata serwisowa', name: 'Imię i nazwisko', email: 'E-mail (wyślemy bilety)', phone: 'Telefon (opcjonalnie)',
    discount: 'Kod rabatowy', terms: 'Akceptuję regulamin sprzedaży. Bilety na wydarzenia z określoną datą nie podlegają zwrotowi, chyba że impreza zostanie odwołana.',
    marketing: 'Chcę dostawać informacje o imprezach klubu (SMS / e-mail). Zgodę możesz wycofać w każdej chwili.',
    lounges: 'Loże i stoliki', loungePick: 'Wybierz lożę na mapie', persons: 'Liczba osób', loungeCta: 'Rezerwuję lożę',
    loungeRequest: 'Wyślij prośbę o rezerwację', loungeSent: 'Prośba o lożę wysłana — klub skontaktuje się z Tobą, żeby ją potwierdzić.',
    taken: 'zajęta', from: 'od', prepay: 'przedpłata online', minSpend: 'minimalny wydatek', inPrice: 'osób w cenie',
    atDoor: 'Bilety kupisz na miejscu.', age: 'Wstęp', cancelled: 'Impreza odwołana', payWith: 'Płatność: BLIK, karta, Apple Pay, Google Pay. Bez zakładania konta.',
    orderTitle: 'Twoje zamówienie', pending: 'Czekamy na potwierdzenie płatności…', paid: 'Opłacone — pokaż kod QR na bramce.',
    cancelledOrder: 'Zamówienie anulowane.', used: 'wykorzystany', notes: 'Uwagi do rezerwacji', total: 'Razem',
  },
  en: {
    events: 'Upcoming events', noEvents: 'No events scheduled yet — check back soon.', tickets: 'Tickets', buy: 'Buy',
    soldOut: 'sold out', ended: 'sales ended', upcoming: 'coming soon', waiting: 'after the current tier sells out',
    fee: 'service fee', name: 'Full name', email: 'E-mail (we will send your tickets)', phone: 'Phone (optional)',
    discount: 'Discount code', terms: 'I accept the terms of sale. Tickets for dated events are non-refundable unless the event is cancelled.',
    marketing: 'Send me news about club events (SMS / e-mail). You can withdraw consent at any time.',
    lounges: 'Tables & lounges', loungePick: 'Pick a table on the map', persons: 'Guests', loungeCta: 'Book the table',
    loungeRequest: 'Send booking request', loungeSent: 'Request sent — the club will contact you to confirm.',
    taken: 'booked', from: 'from', prepay: 'online deposit', minSpend: 'minimum spend', inPrice: 'guests included',
    atDoor: 'Tickets available at the door.', age: 'Entry', cancelled: 'Event cancelled', payWith: 'Pay with BLIK, card, Apple Pay or Google Pay. No account needed.',
    orderTitle: 'Your order', pending: 'Waiting for payment confirmation…', paid: 'Paid — show the QR code at the door.',
    cancelledOrder: 'Order cancelled.', used: 'used', notes: 'Notes', total: 'Total',
  },
} as const;

export function pickLang(param?: string | null, acceptLanguage?: string | null): Lang {
  if (param === 'en' || param === 'pl') return param;
  if (acceptLanguage && !/^pl\b/i.test(acceptLanguage) && /^en\b/i.test(acceptLanguage)) return 'en';
  return 'pl';
}
