import { q } from '@/lib/db';
import { createUser, createOrg } from '@/lib/services/users';
import { createEvent, addTicketType, setEventStatus } from '@/lib/services/events';

let n = 0;

export async function fixture(opts: { provider?: 'none' | 'mock'; plan?: 'start' | 'klub' | 'premium'; feePayer?: 'buyer' | 'org' } = {}) {
  n++;
  const user = await createUser(`manager${n}-${Date.now()}@test.pl`, 'Manager', 'haslo-testowe-123');
  const org = await createOrg(user.id, { name: `Klub Test ${n} ${Date.now()}`, kind: 'club' });
  await q('update orgs set payment_provider = $2, plan = $3, fee_payer = $4 where id = $1',
    [org.id, opts.provider ?? 'mock', opts.plan ?? 'start', opts.feePayer ?? 'buyer']);
  const startsAt = new Date(Date.now() + 2 * 3600_000);
  const event = await createEvent(org.id, { name: `Impreza ${n}`, startsAt, endsAt: new Date(startsAt.getTime() + 6 * 3600_000) });
  await setEventStatus(org.id, event.id, 'published');
  return { user, org, event };
}

export const buyer = (extra: Partial<{ name: string; email: string; marketingConsent: boolean }> = {}) => ({
  name: 'Jan Kowalski', email: `jan${Math.random().toString(36).slice(2)}@test.pl`, termsAccepted: true, ...extra,
});

export { addTicketType };
