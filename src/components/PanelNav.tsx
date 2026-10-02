import Link from 'next/link';
import { logoutAction } from '@/app/(panel)/actions';

export function PanelNav({ org, active, userName }: { org?: { slug: string; name: string; role: string }; active?: string; userName: string }) {
  const links = org
    ? [
        ['wydarzenia', 'Imprezy', `/panel/${org.slug}`],
        ['loze', 'Loże i sala', `/panel/${org.slug}/loze`],
        ['promotorzy', 'Promotorzy', `/panel/${org.slug}/promotorzy`],
        ['goscie', 'Baza gości', `/panel/${org.slug}/goscie`],
        ['ustawienia', 'Ustawienia', `/panel/${org.slug}/ustawienia`],
      ]
    : [];
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <Link href="/panel" className="brand">klub<span>owy</span></Link>
        {org && <strong className="soft">{org.name}</strong>}
        <nav className="nav" aria-label="Panel">
          {links.map(([key, label, href]) => (
            <Link key={key} href={href} className={active === key ? 'on' : ''}>{label}</Link>
          ))}
        </nav>
        <span className="muted" style={{ fontSize: '.85rem' }}>{userName}</span>
        <form action={logoutAction} className="inline">
          <button className="ghost small" type="submit">Wyloguj</button>
        </form>
      </div>
    </header>
  );
}

export function EventTabs({ orgSlug, eventId, active }: { orgSlug: string; eventId: string; active: string }) {
  const base = `/panel/${orgSlug}/wydarzenia/${eventId}`;
  const tabs = [
    ['przeglad', 'Bilety i ustawienia', base],
    ['listy', 'Listy gości', `${base}/listy`],
    ['loze', 'Loże', `${base}/loze`],
    ['bramka', 'Bramka', `${base}/bramka`],
    ['raport', 'Raport na żywo', `${base}/raport`],
  ];
  return (
    <nav className="tabs" aria-label="Impreza">
      {tabs.map(([key, label, href]) => (
        <Link key={key} href={href} className={active === key ? 'on' : ''}>{label}</Link>
      ))}
    </nav>
  );
}
