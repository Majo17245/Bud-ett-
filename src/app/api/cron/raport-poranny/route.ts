import { q } from '@/lib/db';
import { env } from '@/lib/env';
import { sendMail } from '@/lib/mailer';
import { nightSummaryText } from '@/lib/services/reports';

/** Vercel Cron, codziennie rano: podsumowanie nocy dla właścicieli klubów. */
export async function GET(req: Request) {
  if (!env.cronSecret || req.headers.get('authorization') !== `Bearer ${env.cronSecret}`) {
    return new Response('unauthorized', { status: 401 });
  }
  const events = await q<{ id: string; org_id: string; name: string; emails: string[] }>(
    `select e.id, e.org_id, e.name,
       array(select distinct coalesce(o.contact_email, u.email) from memberships m join users u on u.id = m.user_id
             where m.org_id = e.org_id and m.role = 'owner') as emails
     from events e join orgs o on o.id = e.org_id
     where e.status = 'published' and e.ends_at between now() - interval '24 hours' and now()`,
  );
  for (const e of events) {
    const text = await nightSummaryText(e.org_id, e.id, e.name);
    for (const to of e.emails) await sendMail({ to, subject: `Raport po nocy: ${e.name}`, text });
  }
  return Response.json({ sent: events.length });
}
