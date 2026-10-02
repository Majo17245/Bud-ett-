import Link from 'next/link';
import { notFound } from 'next/navigation';
import { headers } from 'next/headers';
import type { Metadata } from 'next';
import { orgBySlug } from '@/lib/services/orgs';
import { publicEvents } from '@/lib/services/events';
import { fmtDate, fmtTime } from '@/lib/time';
import { pickLang, t } from '@/lib/i18n';

export async function generateMetadata({ params }: { params: Promise<{ org: string }> }): Promise<Metadata> {
  const org = await orgBySlug((await params).org);
  return { title: org ? `${org.name} — imprezy i bilety` : 'Klub' };
}

export default async function ClubPage({ params, searchParams }: { params: Promise<{ org: string }>; searchParams: Promise<{ lang?: string }> }) {
  const { org: slug } = await params;
  const sp = await searchParams;
  const org = await orgBySlug(slug);
  if (!org) notFound();
  const lang = pickLang(sp.lang, (await headers()).get('accept-language'));
  const L = t[lang];
  const events = await publicEvents(org.id);
  const q = lang === 'en' ? '?lang=en' : '';
  return (
    <main className="wrap">
      <div className="row between">
        <span className="brand">{org.name}</span>
        <nav className="row" style={{ gap: 8 }}>
          <Link href={`/k/${org.slug}`} className={lang === 'pl' ? 'tag accent' : 'tag'}>PL</Link>
          <Link href={`/k/${org.slug}?lang=en`} className={lang === 'en' ? 'tag accent' : 'tag'}>EN</Link>
        </nav>
      </div>
      <section className="hero">
        <h1>{org.name}</h1>
        <p className="soft">{[org.address ?? org.city, org.instagram && `@${org.instagram}`].filter(Boolean).join(' · ')}</p>
      </section>
      <h2>{L.events}</h2>
      {events.length === 0 && <p className="soft">{L.noEvents}</p>}
      <div className="grid grid-2">
        {events.map((e) => (
          <Link key={e.id} href={`/k/${org.slug}/e/${e.slug}${q}`} className="event-card">
            <div className="event-date">{fmtDate(e.starts_at)} · {fmtTime(e.starts_at)}</div>
            <h3 style={{ margin: '6px 0' }}>{e.name}</h3>
            {e.min_age && <span className="tag">{e.min_age}+</span>}
          </Link>
        ))}
      </div>
      <footer className="site" style={{ marginTop: 48 }}>
        <Link href="/regulamin">Regulamin</Link> · <Link href="/prywatnosc">Prywatność</Link> · bilety obsługuje Klubowy
      </footer>
    </main>
  );
}
