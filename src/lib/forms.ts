import { redirect } from 'next/navigation';
import { UserError } from './db';
import { parseZl } from './money';
import { fromLocalInput } from './time';

export const str = (fd: FormData, k: string) => String(fd.get(k) ?? '').trim();
export const optStr = (fd: FormData, k: string) => str(fd, k) || null;
export const int = (fd: FormData, k: string): number | null => {
  const s = str(fd, k);
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? Math.trunc(n) : null;
};
export const num = (fd: FormData, k: string): number | null => {
  const s = str(fd, k).replace(',', '.');
  if (!s) return null;
  const n = Number(s);
  return Number.isFinite(n) ? n : null;
};
export const money = (fd: FormData, k: string) => parseZl(str(fd, k));
export const date = (fd: FormData, k: string) => fromLocalInput(str(fd, k));
export const bool = (fd: FormData, k: string) => fd.get(k) === 'on' || fd.get(k) === 'true' || fd.get(k) === '1';

export function withMessage(path: string, kind: 'ok' | 'blad', msg: string) {
  const [base, hash] = path.split('#');
  const url = new URL(base, 'http://x');
  url.searchParams.delete('ok');
  url.searchParams.delete('blad');
  url.searchParams.set(kind, msg);
  return url.pathname + url.search + (hash ? '#' + hash : '');
}

/**
 * Wykonuje akcję formularza i wraca na stronę z komunikatem. Błędy biznesowe (UserError)
 * pokazujemy użytkownikowi, pozostałe lecą dalej (logi + strona błędu).
 * fn może zwrócić { ok, to } — komunikat i/lub inny adres powrotu.
 */
export async function act(back: string, fn: () => Promise<string | { ok?: string; to?: string } | void>): Promise<never> {
  let target: string;
  try {
    const r = await fn();
    const res = typeof r === 'string' ? { ok: r } : r ?? {};
    target = res.ok ? withMessage(res.to ?? back, 'ok', res.ok) : res.to ?? back;
  } catch (e) {
    if (e instanceof UserError) target = withMessage(back, 'blad', e.message);
    else throw e;
  }
  redirect(target);
}
