/**
 * Dane demonstracyjne: klub, impreza z pulami biletów, loże, promotorzy i 300 fikcyjnych
 * zaproszeń do "testu na sucho" bramki (plan ekspresowy z biznesplanu).
 * Użycie: DATABASE_URL=... APP_SECRET=... npm run db:seed
 */
import { pool, q } from '../src/lib/db';
import { createUser, createOrg } from '../src/lib/services/users';
import { createEvent, addTicketType, setEventStatus } from '../src/lib/services/events';
import { createLounge } from '../src/lib/services/lounges';
import { createPromoter } from '../src/lib/services/promoters';
import { createList, addGuests } from '../src/lib/services/lists';
import { createDoorToken } from '../src/lib/services/door';
import { nextWeekdayAt } from '../src/lib/time';

const FIRST = ['Anna', 'Jan', 'Kasia', 'Piotr', 'Ola', 'Michał', 'Zuzanna', 'Kuba', 'Natalia', 'Tomasz', 'Julia', 'Bartek', 'Maja', 'Kacper', 'Wiktoria', 'Szymon', 'Lena', 'Filip', 'Hanna', 'Adam'];
const LAST = ['Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kamiński', 'Lewandowski', 'Zieliński', 'Szymański', 'Woźniak', 'Dąbrowski', 'Kozłowski', 'Jankowski', 'Mazur', 'Kwiatkowski', 'Krawczyk', 'Piotrowski', 'Grabowski', 'Nowakowski', 'Pawłowski', 'Michalski'];

async function main() {
  const email = process.env.SEED_EMAIL ?? 'demo@klubowy.local';
  const password = process.env.SEED_PASSWORD ?? 'demo-haslo-123';
  const existing = await q<{ id: string }>('select id from users where lower(email) = $1', [email]);
  if (existing.length) {
    console.log(`Dane demo już istnieją (${email}). Pomijam.`);
    return;
  }
  const user = await createUser(email, 'Manager Demo', password);
  const org = await createOrg(user.id, { name: 'Klub Demo', kind: 'club', city: 'Lublin' });
  await q(`update orgs set capacity = 600, address = 'ul. Przykładowa 1, Lublin', contact_email = $2, payment_provider = $3, plan = 'klub' where id = $1`,
    [org.id, email, process.env.ALLOW_MOCK_PAYMENTS === 'true' ? 'mock' : 'none']);

  const start = nextWeekdayAt(5, 22); // najbliższy piątek, 22:00
  const end = new Date(start.getTime() + 7 * 3600_000);
  const ev = await createEvent(org.id, {
    name: 'Noc testowa — Friday Party', startsAt: start, endsAt: end, capacity: 600, minAge: 18,
    description: 'Najlepsze hity, dwa parkiety i loże VIP. Wejście 18+.',
  });
  await addTicketType(ev.id, { name: 'Early bird', price: 2500, quantity: 100 });
  await addTicketType(ev.id, { name: 'I pula', price: 3500, quantity: 200 });
  await addTicketType(ev.id, { name: 'II pula', price: 4500, quantity: 200 });
  await addTicketType(ev.id, { tierGroup: 'Bilety grupowe', name: 'Paczka 4 osoby', price: 12000, quantity: 25, groupSize: 4 });
  await setEventStatus(org.id, ev.id, 'published');

  const lounges = [
    { name: 'Loża 1', x: 6, y: 12 }, { name: 'Loża 2', x: 6, y: 34 }, { name: 'Loża 3', x: 6, y: 56 },
    { name: 'Loża VIP', x: 78, y: 12, vip: true }, { name: 'Stolik 5', x: 78, y: 40 }, { name: 'Stolik 6', x: 78, y: 62 },
  ];
  for (const l of lounges) {
    await createLounge(org.id, {
      name: l.name, zone: l.vip ? 'Antresola' : 'Sala główna', capacity: l.vip ? 8 : 6, maxCapacity: l.vip ? 12 : 8,
      basePrice: l.vip ? 150000 : 60000, extraPersonPrice: l.vip ? 15000 : 8000, minSpend: l.vip ? 150000 : 60000,
      prepayPercent: 50, mapX: l.x, mapY: l.y, mapW: 16, mapH: 16,
    });
  }

  const promoters = [];
  for (const name of ['Kamil', 'Ola', 'Damian']) {
    promoters.push(await createPromoter(org.id, { name, ticketCommissionPct: 10, guestCommission: 300 }));
  }

  // 300 fikcyjnych zaproszeń w 4 listach (test na sucho).
  const listsSpec = [
    { name: 'Lista Kamila', capacity: 100, promoterId: promoters[0].id },
    { name: 'Lista Oli', capacity: 100, promoterId: promoters[1].id },
    { name: 'Lista Damiana', capacity: 100, promoterId: promoters[2].id },
    { name: 'Urodziny i goście klubu', capacity: 120, promoterId: null },
  ];
  let n = 0;
  for (const spec of listsSpec) {
    const list = await createList(ev.id, { name: spec.name, capacity: spec.capacity, promoterId: spec.promoterId, entryUntil: new Date(start.getTime() + 2 * 3600_000) });
    const guests = [];
    for (let i = 0; i < 75; i++, n++) guests.push({ fullName: `${FIRST[n % 20]} ${LAST[Math.floor(n / 20) % 20]} ${n + 1}`, plusOnes: n % 7 === 0 ? 1 : 0 });
    await addGuests(list!.id, guests, 'seed');
  }
  const doorToken = await createDoorToken(ev.id, 'Bramka główna');
  const appUrl = process.env.APP_URL ?? 'http://localhost:3000';
  console.log(`
Gotowe.
  Panel:     ${appUrl}/logowanie   (${email} / ${password})
  Strona:    ${appUrl}/k/${org.slug}
  Bramka:    ${appUrl}/bramka/${ev.id}#t=${doorToken}
  Promotor:  ${appUrl}/promotor/${promoters[0].panelToken}
  Zaproszeń: ${n}`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(() => pool().end());
