import { NextResponse, type NextRequest } from 'next/server';

/** "bilety.klubx.pl=klubx,..." → mapa domena → slug klubu */
function customDomains(): Map<string, string> {
  return new Map(
    (process.env.CUSTOM_DOMAINS ?? '')
      .split(',')
      .map((p) => p.trim().split('='))
      .filter((p) => p.length === 2 && p[0] && p[1])
      .map(([d, s]) => [d.toLowerCase(), s]),
  );
}

export function proxy(req: NextRequest) {
  const url = req.nextUrl;
  const host = (req.headers.get('host') ?? '').toLowerCase().split(':')[0];
  const orgForDomain = customDomains().get(host);

  let res: NextResponse;
  if (orgForDomain && !url.pathname.startsWith('/k/') && !/^\/(zamowienie|zaproszenie|platnosc-testowa|regulamin|prywatnosc|api|_next)/.test(url.pathname)) {
    // Własna domena klubu: bilety.klubx.pl/e/impreza → /k/klubx/e/impreza
    const rewritten = url.clone();
    rewritten.pathname = `/k/${orgForDomain}${url.pathname === '/' ? '' : url.pathname}`;
    res = NextResponse.rewrite(rewritten);
  } else {
    res = NextResponse.next();
  }

  // Link promotora (?p=KOD) — zapamiętujemy na 30 dni, żeby sprzedaż przypisała się także przy późniejszym zakupie.
  const p = url.searchParams.get('p');
  const m = url.pathname.match(/^\/k\/([a-z0-9-]+)/) ?? (orgForDomain ? [null, orgForDomain] : null);
  if (p && m?.[1] && /^[A-Za-z0-9]{3,16}$/.test(p)) {
    res.cookies.set(`ref_${m[1]}`, p.toUpperCase(), { maxAge: 60 * 60 * 24 * 30, sameSite: 'lax', httpOnly: true, path: '/' });
  }
  return res;
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|sw.js|manifest.webmanifest|icon.svg|favicon.ico).*)'],
};
