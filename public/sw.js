/* Service worker skanera bramki: powłoka aplikacji i skrypty z cache, gdy w klubie nie ma zasięgu.
   Dane (manifest kodów, kolejka skanów) trzyma sama aplikacja w IndexedDB. */
const CACHE = 'bramka-v1';

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k.startsWith('bramka-') && k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin || url.pathname.startsWith('/api/')) return;

  // Strona skanera: najpierw sieć (świeża wersja), bez sieci — ostatnia zapisana.
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req)
        .then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(url.pathname, copy));
          }
          return res;
        })
        .catch(() => caches.match(url.pathname).then((r) => r || new Response('Brak połączenia — otwórz skaner raz z internetem przed imprezą.', { status: 503, headers: { 'Content-Type': 'text/plain; charset=utf-8' } }))),
    );
    return;
  }

  // Skrypty, style, czcionki: z cache, a w tle z sieci.
  if (url.pathname.startsWith('/_next/static/') || /\.(js|css|woff2?|svg|png|ico|webmanifest)$/.test(url.pathname)) {
    event.respondWith(
      caches.match(req).then((cached) => {
        const network = fetch(req).then((res) => {
          if (res.ok) {
            const copy = res.clone();
            caches.open(CACHE).then((c) => c.put(req, copy));
          }
          return res;
        });
        return cached || network;
      }),
    );
  }
});
