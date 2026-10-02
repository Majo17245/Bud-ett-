export const TZ = 'Europe/Warsaw';

const dtf = new Intl.DateTimeFormat('pl-PL', {
  timeZone: TZ, weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
});
const df = new Intl.DateTimeFormat('pl-PL', { timeZone: TZ, weekday: 'long', day: 'numeric', month: 'long' });
const tf = new Intl.DateTimeFormat('pl-PL', { timeZone: TZ, hour: '2-digit', minute: '2-digit' });

export const fmtDateTime = (d: Date | string) => dtf.format(new Date(d));
export const fmtDate = (d: Date | string) => df.format(new Date(d));
export const fmtTime = (d: Date | string) => tf.format(new Date(d));

/** Wartość dla <input type="datetime-local"> w strefie klubu. */
export function toLocalInput(d: Date | string | null | undefined): string {
  if (!d) return '';
  const parts = new Intl.DateTimeFormat('sv-SE', {
    timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
  }).format(new Date(d));
  return parts.replace(' ', 'T');
}

/** "2026-10-16T22:00" w strefie klubu → Date (UTC). */
export function fromLocalInput(s: string | null | undefined): Date | null {
  if (!s || !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(s)) return null;
  const [datePart, timePart] = s.split('T');
  const [y, mo, d] = datePart.split('-').map(Number);
  const [h, mi] = timePart.split(':').map(Number);
  // Zgadujemy przesunięcie strefy i korygujemy (działa też na zmianę czasu).
  let guess = Date.UTC(y, mo - 1, d, h, mi);
  for (let i = 0; i < 2; i++) {
    const local = toLocalInput(new Date(guess));
    const [ld, lt] = local.split('T');
    const [ly, lmo, ldd] = ld.split('-').map(Number);
    const [lh, lmi] = lt.split(':').map(Number);
    const diff = Date.UTC(ly, lmo - 1, ldd, lh, lmi) - Date.UTC(y, mo - 1, d, h, mi);
    guess -= diff;
  }
  return new Date(guess);
}

/** Najbliższy dany dzień tygodnia (0 = niedziela) o podanej godzinie czasu klubu, nie wcześniej niż jutro. */
export function nextWeekdayAt(weekday: number, hour: number, minute = 0): Date {
  const today = toLocalInput(new Date()).slice(0, 10);
  const [y, m, d] = today.split('-').map(Number);
  const base = new Date(Date.UTC(y, m - 1, d));
  const add = (weekday - base.getUTCDay() + 7) % 7 || 7;
  base.setUTCDate(base.getUTCDate() + add);
  const iso = base.toISOString().slice(0, 10);
  return fromLocalInput(`${iso}T${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`)!;
}
