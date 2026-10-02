'use client';

import jsQR from 'jsqr';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { ManifestEntry } from '@/lib/services/door';
import { idbGet, idbSet } from './store';

type Manifest = {
  event: { id: string; name: string; starts_at: string; ends_at: string; capacity: number | null; min_age: number | null; org_name: string };
  entries: ManifestEntry[];
  summary: { inside: number; entered: number; scans: number; cursor: number };
  generatedAt: string;
};
type QueuedEvent = { clientId: string; type: 'scan' | 'in' | 'out'; code?: string; persons?: number; override?: boolean; at: string };
type Result = 'ok' | 'override' | 'duplicate' | 'invalid' | 'void' | 'too_late' | 'counter';
type LogItem = { clientId: string; code: string; result: Result; label: string; persons: number; at: string; corrected?: Result };

const RESULT_TEXT: Record<Result, string> = {
  ok: 'WEJŚCIE OK', override: 'WPUSZCZONY RĘCZNIE', duplicate: 'JUŻ UŻYTY', invalid: 'NIEZNANY KOD', void: 'UNIEWAŻNIONY',
  too_late: 'LISTA PO CZASIE', counter: '',
};
const KIND_TEXT: Record<string, string> = { ticket: 'Bilet', guest: 'Lista', lounge: 'Loża', external: 'Inna platforma' };
const okResult = (r: Result) => r === 'ok' || r === 'override';

function uid() {
  return (crypto.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`).replace(/-/g, '').slice(0, 32);
}

function normalize(s: string) {
  return s.toLowerCase().replace(/ł/g, 'l').normalize('NFD').replace(/[̀-ͯ]/g, '');
}

function beep(ok: boolean) {
  try {
    const Ctx = window.AudioContext ?? (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
    const ctx = new Ctx();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.frequency.value = ok ? 880 : 220;
    o.type = ok ? 'sine' : 'square';
    g.gain.value = 0.15;
    o.connect(g).connect(ctx.destination);
    o.start();
    o.stop(ctx.currentTime + (ok ? 0.12 : 0.4));
    o.onended = () => ctx.close();
  } catch {}
  navigator.vibrate?.(ok ? 60 : [120, 60, 120]);
}

export function Scanner({ eventId }: { eventId: string }) {
  const [token, setToken] = useState<string | null>(null);
  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [used, setUsed] = useState<Set<string>>(new Set());
  const [queue, setQueue] = useState<QueuedEvent[]>([]);
  const [log, setLog] = useState<LogItem[]>([]);
  const [online, setOnline] = useState(true);
  const [lastSync, setLastSync] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [overlay, setOverlay] = useState<LogItem | null>(null);
  const [camera, setCamera] = useState<'off' | 'on' | 'error'>('off');
  const [manual, setManual] = useState('');
  const [ready, setReady] = useState(false);

  const deviceId = useRef<string>('');
  const cursor = useRef(0);
  const syncing = useRef(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const lastCode = useRef<{ code: string; at: number }>({ code: '', at: 0 });
  const overlayUntil = useRef(0);
  const stateRef = useRef({ manifest, used, queue });
  stateRef.current = { manifest, used, queue };

  const byCode = useMemo(() => {
    const m = new Map<string, ManifestEntry>();
    for (const e of manifest?.entries ?? []) m.set(e.c, e);
    return m;
  }, [manifest]);

  const k = (name: string) => `${name}:${eventId}`;

  // ---------- start: token, urządzenie, dane lokalne ----------
  useEffect(() => {
    const hash = new URLSearchParams(location.hash.slice(1));
    const fromHash = hash.get('t');
    try {
      if (fromHash) {
        localStorage.setItem(k('token'), fromHash);
        history.replaceState(null, '', location.pathname); // token nie zostaje w pasku adresu
      }
      setToken(fromHash ?? localStorage.getItem(k('token')));
      deviceId.current = localStorage.getItem('deviceId') ?? 'dev-' + uid().slice(0, 12);
      localStorage.setItem('deviceId', deviceId.current);
    } catch {
      deviceId.current = 'dev-' + uid().slice(0, 12);
    }
    setOnline(navigator.onLine);
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    addEventListener('online', on);
    addEventListener('offline', off);
    navigator.serviceWorker?.register('/sw.js', { scope: '/bramka/' }).catch(() => {});
    (async () => {
      const [m, u, qd, c, l] = await Promise.all([
        idbGet<Manifest>(k('manifest')), idbGet<string[]>(k('used')), idbGet<QueuedEvent[]>(k('queue')), idbGet<number>(k('cursor')), idbGet<LogItem[]>(k('log')),
      ]).catch(() => [undefined, undefined, undefined, undefined, undefined] as const);
      if (m) setManifest(m);
      if (u) setUsed(new Set(u));
      if (qd) setQueue(qd);
      if (c) cursor.current = c;
      if (l) setLog(l);
      setReady(true);
    })();
    // Ekran nie gaśnie podczas pracy na bramce.
    let lock: { release: () => Promise<void> } | null = null;
    (navigator as unknown as { wakeLock?: { request: (t: string) => Promise<typeof lock> } }).wakeLock?.request('screen').then((l) => { lock = l; }).catch(() => {});
    return () => {
      removeEventListener('online', on);
      removeEventListener('offline', off);
      lock?.release().catch(() => {});
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId]);

  // Zapis stanu lokalnego przy każdej zmianie.
  useEffect(() => { if (ready) idbSet(k('used'), [...used]).catch(() => {}); }, [used, ready]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (ready) idbSet(k('queue'), queue).catch(() => {}); }, [queue, ready]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { if (ready) idbSet(k('log'), log.slice(0, 50)).catch(() => {}); }, [log, ready]); // eslint-disable-line react-hooks/exhaustive-deps

  const authHeaders = useCallback((): HeadersInit => (token ? { Authorization: `Bearer ${token}` } : {}), [token]);

  // ---------- pobranie manifestu ----------
  const loadManifest = useCallback(async () => {
    try {
      const res = await fetch(`/api/door/${eventId}/manifest`, { headers: authHeaders(), cache: 'no-store' });
      if (res.status === 401) {
        setError('Brak dostępu: otwórz skaner z linku od managera albo zaloguj się do panelu.');
        return;
      }
      if (!res.ok) throw new Error(String(res.status));
      const m = (await res.json()) as Manifest;
      setManifest(m);
      setError(null);
      cursor.current = Math.max(cursor.current, m.summary.cursor);
      await idbSet(k('manifest'), m);
      await idbSet(k('cursor'), cursor.current);
      setUsed((prev) => {
        const next = new Set(prev);
        for (const e of m.entries) if (e.x) next.add(e.c);
        return next;
      });
    } catch {
      setOnline(navigator.onLine);
    }
  }, [eventId, authHeaders]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { if (ready) loadManifest(); }, [ready, loadManifest]);

  // ---------- synchronizacja ----------
  const sync = useCallback(async () => {
    if (syncing.current || !stateRef.current.manifest) return;
    syncing.current = true;
    const batch = stateRef.current.queue.slice(0, 200);
    try {
      const res = await fetch(`/api/door/${eventId}/sync`, {
        method: 'POST', headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ deviceId: deviceId.current, cursor: cursor.current, events: batch }),
      });
      if (!res.ok) throw new Error(String(res.status));
      const data = (await res.json()) as { results: { clientId: string; result: Result }[]; usedCodes: string[]; summary: Manifest['summary'] };
      const sent = new Set(batch.map((b) => b.clientId));
      setQueue((q) => q.filter((e) => !sent.has(e.clientId)));
      const verdict = new Map(data.results.map((r) => [r.clientId, r.result]));
      setLog((l) => l.map((it) => (verdict.has(it.clientId) && verdict.get(it.clientId) !== it.result ? { ...it, corrected: verdict.get(it.clientId) } : it)));
      if (data.usedCodes.length) setUsed((prev) => new Set([...prev, ...data.usedCodes]));
      cursor.current = data.summary.cursor;
      idbSet(k('cursor'), cursor.current).catch(() => {});
      setManifest((m) => (m ? { ...m, summary: data.summary } : m));
      setOnline(true);
      setLastSync(new Date());
    } catch {
      setOnline(false);
    } finally {
      syncing.current = false;
    }
  }, [eventId, authHeaders]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!ready) return;
    const t = setInterval(() => {
      if (stateRef.current.queue.length || Date.now() % 15000 < 3000) sync();
    }, 3000);
    return () => clearInterval(t);
  }, [ready, sync]);

  // ---------- obsługa kodu ----------
  const record = useCallback((ev: QueuedEvent) => setQueue((q) => [...q, ev]), []);

  const handleCode = useCallback((raw: string, opts: { override?: boolean } = {}) => {
    const code = raw.trim();
    if (!code) return;
    const { used: u } = stateRef.current;
    const entry = byCode.get(code) ?? byCode.get(code.toUpperCase());
    let result: Result;
    if (!entry) result = 'invalid';
    else if (entry.v) result = 'void';
    else if (u.has(entry.c)) result = 'duplicate';
    else if (entry.u && Date.now() > new Date(entry.u).getTime()) result = opts.override ? 'override' : 'too_late';
    else result = 'ok';
    const clientId = uid();
    const item: LogItem = {
      clientId, code: entry?.c ?? code, result, persons: entry?.p ?? 1, at: new Date().toISOString(),
      label: entry ? `${entry.n || KIND_TEXT[entry.k]} · ${entry.i}` : code,
    };
    if (okResult(result) && entry) setUsed((prev) => new Set(prev).add(entry.c));
    // Do serwera trafia każdy skan (także odrzucony) — raport pokaże próby wejścia na cudzy kod.
    record({ clientId, type: 'scan', code: entry?.c ?? code, override: opts.override, at: item.at });
    setLog((l) => [item, ...l].slice(0, 50));
    setOverlay(item);
    overlayUntil.current = Date.now() + (okResult(result) ? 1400 : 2600);
    beep(okResult(result));
  }, [byCode, record]);

  useEffect(() => {
    if (!overlay) return;
    const t = setTimeout(() => setOverlay((o) => (o?.clientId === overlay.clientId ? null : o)), okResult(overlay.result) ? 1400 : 2600);
    return () => clearTimeout(t);
  }, [overlay]);

  // ---------- kamera ----------
  useEffect(() => {
    if (camera !== 'on') return;
    let stream: MediaStream | null = null;
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const Detector = (window as unknown as { BarcodeDetector?: new (o: { formats: string[] }) => { detect: (s: CanvasImageSource) => Promise<{ rawValue: string }[]> } }).BarcodeDetector;
    const detector = Detector ? new Detector({ formats: ['qr_code', 'code_128', 'ean_13'] }) : null;

    const onCode = (value: string) => {
      const now = Date.now();
      if (now < overlayUntil.current) return;
      if (value === lastCode.current.code && now - lastCode.current.at < 4000) return;
      lastCode.current = { code: value, at: now };
      handleCode(value);
    };

    const tick = async () => {
      if (stopped) return;
      const v = videoRef.current;
      if (v && v.readyState >= 2) {
        try {
          if (detector) {
            const codes = await detector.detect(v);
            if (codes[0]?.rawValue) onCode(codes[0].rawValue);
          } else if (canvasRef.current) {
            const c = canvasRef.current;
            const scale = Math.min(1, 640 / v.videoWidth);
            c.width = Math.round(v.videoWidth * scale);
            c.height = Math.round(v.videoHeight * scale);
            const ctx = c.getContext('2d', { willReadFrequently: true })!;
            ctx.drawImage(v, 0, 0, c.width, c.height);
            const img = ctx.getImageData(0, 0, c.width, c.height);
            const found = jsQR(img.data, img.width, img.height, { inversionAttempts: 'dontInvert' });
            if (found?.data) onCode(found.data);
          }
        } catch {}
      }
      timer = setTimeout(tick, 120);
    };

    navigator.mediaDevices
      ?.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false })
      .then(async (s) => {
        stream = s;
        if (videoRef.current) {
          videoRef.current.srcObject = s;
          await videoRef.current.play().catch(() => {});
        }
        tick();
      })
      .catch(() => setCamera('error'));
    return () => {
      stopped = true;
      clearTimeout(timer);
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [camera, handleCode]);

  // ---------- licznik w sali (serwer + niezsynchronizowane lokalne zdarzenia) ----------
  const pendingLog = new Map(log.map((l) => [l.clientId, l]));
  let delta = 0;
  for (const e of queue) {
    if (e.type === 'in') delta += e.persons ?? 1;
    else if (e.type === 'out') delta -= e.persons ?? 1;
    else {
      const it = pendingLog.get(e.clientId);
      if (it && okResult(it.result)) delta += it.persons;
    }
  }
  const inside = Math.max(0, (manifest?.summary.inside ?? 0) + delta);
  const capacity = manifest?.event.capacity ?? null;

  const search = manual.trim().length >= 3 && !/^[TGL][0-9A-Z]{6,}$/i.test(manual.trim())
    ? (manifest?.entries ?? []).filter((e) => normalize(e.n).includes(normalize(manual.trim()))).slice(0, 8)
    : [];

  if (!ready) return <main className="narrow"><p className="soft">Uruchamianie skanera…</p></main>;

  return (
    <main style={{ maxWidth: 560, margin: '0 auto', padding: '12px 12px 120px' }}>
      <header className="row between" style={{ marginBottom: 10 }}>
        <div>
          <div className="muted" style={{ fontSize: '.8rem' }}>{manifest?.event.org_name ?? 'Bramka'}</div>
          <strong>{manifest?.event.name ?? 'Ładowanie listy…'}</strong>
        </div>
        <span className={`tag ${online ? 'ok' : 'warn'}`}>{online ? 'online' : 'offline'}{queue.length ? ` · ${queue.length} do wysłania` : ''}</span>
      </header>

      {error && <div className="flash bad">{error}</div>}
      {!manifest && !error && <div className="flash info">Pobieram listę kodów… Pierwsze uruchomienie wymaga internetu.</div>}

      <div className="stats" style={{ gridTemplateColumns: '1fr 1fr' }}>
        <div className="stat">
          <b>{inside}{capacity ? <small className="muted" style={{ fontSize: '1rem' }}> / {capacity}</small> : null}</b><span>w sali</span>
          {capacity ? <div className="bar"><i style={{ width: `${Math.min(100, (inside / capacity) * 100)}%`, background: inside >= capacity ? 'var(--bad)' : undefined }} /></div> : null}
        </div>
        <div className="stat"><b>{manifest?.entries.length ?? 0}</b><span>kodów w telefonie · {lastSync ? `sync ${lastSync.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}` : 'bez synchronizacji'}</span></div>
      </div>
      {capacity && inside >= capacity && <div className="flash bad">Osiągnięto limit osób w sali — wpuszczaj tylko po wyjściach.</div>}

      <div className="card" style={{ padding: 0, overflow: 'hidden', position: 'relative', background: '#000' }}>
        {camera === 'on' ? (
          <video ref={videoRef} playsInline muted style={{ width: '100%', display: 'block', aspectRatio: '4 / 3', objectFit: 'cover' }} />
        ) : (
          <div style={{ aspectRatio: '4 / 3', display: 'grid', placeItems: 'center', padding: 16, textAlign: 'center' }}>
            <div>
              {camera === 'error' && <p className="soft">Brak dostępu do aparatu. Zezwól na kamerę w ustawieniach przeglądarki albo wpisuj kody ręcznie.</p>}
              <button onClick={() => setCamera('on')} disabled={!manifest}>Włącz skanowanie</button>
            </div>
          </div>
        )}
        <canvas ref={canvasRef} hidden />
        {overlay && (
          <button
            onClick={() => setOverlay(null)}
            style={{
              position: 'absolute', inset: 0, borderRadius: 0, flexDirection: 'column', whiteSpace: 'normal', padding: 16,
              background: okResult(overlay.result) ? 'rgba(25, 135, 84, .96)' : overlay.result === 'too_late' ? 'rgba(201, 125, 16, .96)' : 'rgba(190, 40, 30, .96)',
              color: '#fff',
            }}
          >
            <span style={{ fontSize: '2rem', fontWeight: 800 }}>{RESULT_TEXT[overlay.result]}</span>
            {okResult(overlay.result) && overlay.persons > 1 && <span style={{ fontSize: '1.6rem', fontWeight: 700 }}>{overlay.persons} OSOBY</span>}
            <span style={{ fontSize: '1rem', fontWeight: 500, marginTop: 8 }}>{overlay.label}</span>
          </button>
        )}
      </div>

      {log[0]?.result === 'too_late' && !used.has(log[0].code) && (
        <button className="block" style={{ background: 'var(--warn)', marginBottom: 12 }} onClick={() => handleCode(log[0].code, { override: true })}>
          Wpuść mimo to (decyzja managera)
        </button>
      )}

      <div className="row" style={{ marginBottom: 12, flexWrap: 'nowrap' }}>
        <button className="ghost" style={{ flex: 1 }} onClick={() => record({ clientId: uid(), type: 'in', persons: 1, at: new Date().toISOString() })}>+1 wejście (kasa)</button>
        <button className="ghost" style={{ flex: 1 }} onClick={() => record({ clientId: uid(), type: 'out', persons: 1, at: new Date().toISOString() })}>−1 wyjście</button>
      </div>

      <form
        className="card"
        onSubmit={(e) => {
          e.preventDefault();
          if (manual.trim()) handleCode(manual);
          setManual('');
        }}
      >
        <label htmlFor="manual">Kod z biletu albo nazwisko z listy</label>
        <div className="row" style={{ flexWrap: 'nowrap' }}>
          <input id="manual" value={manual} onChange={(e) => setManual(e.target.value)} autoComplete="off" autoCapitalize="characters" placeholder="np. G7K2… lub Kowalski" />
          <button type="submit">Sprawdź</button>
        </div>
        {search.length > 0 && (
          <ul style={{ listStyle: 'none', padding: 0, margin: '8px 0 0' }}>
            {search.map((e) => (
              <li key={e.c} className="row between" style={{ padding: '6px 0', borderBottom: '1px solid var(--line)' }}>
                <span>{e.n} <span className="muted">· {e.i}{e.p > 1 ? ` · ${e.p} os.` : ''}</span></span>
                {used.has(e.c) ? <span className="tag">wszedł</span> : <button type="button" className="small" onClick={() => { handleCode(e.c); setManual(''); }}>Wpuść</button>}
              </li>
            ))}
          </ul>
        )}
      </form>

      <section className="card">
        <h3>Ostatnie skany</h3>
        {log.length === 0 && <p className="muted">Jeszcze nic.</p>}
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {log.slice(0, 15).map((it) => (
            <li key={it.clientId} style={{ padding: '6px 0', borderBottom: '1px solid var(--line)', fontSize: '.9rem' }}>
              <span className={`tag ${okResult(it.result) ? 'ok' : it.result === 'too_late' ? 'warn' : 'bad'}`}>{RESULT_TEXT[it.result]}</span>{' '}
              {it.label}
              <span className="muted"> · {new Date(it.at).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}</span>
              {it.corrected && <div className="muted" style={{ color: 'var(--warn)' }}>Serwer: {RESULT_TEXT[it.corrected] || it.corrected} — inny telefon wpuścił ten kod wcześniej.</div>}
            </li>
          ))}
        </ul>
      </section>
      <p className="muted" style={{ fontSize: '.8rem' }}>
        Skaner działa bez internetu: kody są w telefonie, a wejścia wyślą się same po odzyskaniu zasięgu. Urządzenie: {deviceId.current}
      </p>
    </main>
  );
}
