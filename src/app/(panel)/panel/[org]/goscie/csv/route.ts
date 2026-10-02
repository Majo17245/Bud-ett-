import { cookies } from 'next/headers';
import { q } from '@/lib/db';
import { SESSION_COOKIE } from '@/lib/session';
import { membership, userForSession } from '@/lib/services/users';

const cell = (v: unknown) => {
  const s = v == null ? '' : String(v);
  // Ochrona przed wstrzyknięciem formuł w Excelu.
  const safe = /^[=+\-@]/.test(s) ? "'" + s : s;
  return '"' + safe.replace(/"/g, '""') + '"';
};

export async function GET(_req: Request, { params }: { params: Promise<{ org: string }> }) {
  const { org: slug } = await params;
  const user = await userForSession((await cookies()).get(SESSION_COOKIE)?.value);
  const org = user ? await membership(user.id, slug) : null;
  if (!org || !['owner', 'manager'].includes(org.role)) return new Response('Brak dostępu', { status: 403 });
  const rows = await q<{ name: string | null; email: string | null; phone: string | null; consent_at: Date | null; consent_source: string | null; orders_count: number }>(
    `select name, email, phone, consent_at, consent_source, orders_count from guests
     where org_id = $1 and marketing_consent and anonymized_at is null order by last_seen_at desc`,
    [org.id],
  );
  const lines = [['imie_nazwisko', 'email', 'telefon', 'zgoda_od', 'zrodlo_zgody', 'zamowienia'].join(';')];
  for (const r of rows) lines.push([r.name, r.email, r.phone, r.consent_at?.toISOString(), r.consent_source, r.orders_count].map(cell).join(';'));
  return new Response('﻿' + lines.join('\n'), {
    headers: {
      'Content-Type': 'text/csv; charset=utf-8',
      'Content-Disposition': `attachment; filename="goscie-${slug}.csv"`,
      'Cache-Control': 'no-store',
    },
  });
}
