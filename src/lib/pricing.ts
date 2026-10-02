/**
 * Cennik z biznesplanu ("Biznesplan: model przychodów i cennik").
 * Opłaty zawierają koszty płatności. Kwoty w groszach.
 */
export type Plan = 'start' | 'klub' | 'premium';
export type FeePayer = 'buyer' | 'org';

export const PLANS: Record<Plan, {
  label: string;
  monthly: number;
  extraVenueMonthly: number;
  ticketPct: number;
  minTicketFee: number;
  loungePct: number;
  features: string[];
}> = {
  start: {
    label: 'Start',
    monthly: 0,
    extraVenueMonthly: 0,
    ticketPct: 5,
    minTicketFee: 149,
    loungePct: 2.5,
    features: ['strona i sprzedaż', 'BLIK', 'bramka offline', 'listy gości', 'raporty'],
  },
  klub: {
    label: 'Klub',
    monthly: 29_900,
    extraVenueMonthly: 0,
    ticketPct: 5,
    minTicketFee: 149,
    loungePct: 2.5,
    features: ['to co Start', 'loże na mapie sali', 'panel promotorów', 'baza gości', '500 SMS-ów/mies.', 'wsparcie w nocy'],
  },
  premium: {
    label: 'Premium',
    monthly: 79_900,
    extraVenueMonthly: 19_900,
    ticketPct: 4,
    // Biznesplan nie podaje minimum dla Premium — przyjmujemy to samo co w Start (do potwierdzenia).
    minTicketFee: 149,
    loungePct: 2,
    features: ['to co Klub', 'import z platform', 'asystent DM', 'mObywatel', 'KSeF', 'automatyczne prowizje', 'opiekun'],
  },
};

export const ADDONS = {
  onsiteSetup: 99_000,
  smsOverPackage: 12,
  doorKitPerEvent: 4_900,
  websiteDesign: 149_000,
};

export function ticketFee(unitPrice: number, plan: Plan): number {
  if (unitPrice <= 0) return 0;
  const p = PLANS[plan];
  return Math.max(Math.round((unitPrice * p.ticketPct) / 100), p.minTicketFee);
}

export function loungeFee(prepayAmount: number, plan: Plan): number {
  if (prepayAmount <= 0) return 0;
  return Math.round((prepayAmount * PLANS[plan].loungePct) / 100);
}

export function applyDiscount(unitPrice: number, percentOff: number | null | undefined): number {
  if (!percentOff) return unitPrice;
  return Math.round((unitPrice * (100 - percentOff)) / 100);
}

export type PricedLine = { quantity: number; unitPrice: number; unitFee: number };

export function orderTotals(lines: PricedLine[], feePayer: FeePayer) {
  const subtotal = lines.reduce((s, l) => s + l.quantity * l.unitPrice, 0);
  const fee = lines.reduce((s, l) => s + l.quantity * l.unitFee, 0);
  const total = feePayer === 'buyer' ? subtotal + fee : subtotal;
  // Ile zostaje klubowi po naszej opłacie (koszty operatora płatności są w niej zawarte).
  const clubNet = feePayer === 'buyer' ? subtotal : subtotal - fee;
  return { subtotal, fee, total, clubNet };
}

/** Cena loży: cena bazowa za `capacity` osób + dopłata za każdą kolejną osobę. */
export function loungePrice(l: { capacity: number; max_capacity: number; base_price: number; extra_person_price: number; prepay_percent: number }, persons: number) {
  if (!Number.isInteger(persons) || persons < 1 || persons > l.max_capacity) {
    throw new RangeError(`Liczba osób musi być od 1 do ${l.max_capacity}`);
  }
  const extra = Math.max(0, persons - l.capacity);
  const total = l.base_price + extra * l.extra_person_price;
  const prepay = Math.ceil((total * l.prepay_percent) / 100);
  return { total, prepay };
}
