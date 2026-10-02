/** Formatuje grosze jako "1 234,50 zł" (bez groszy, gdy kwota jest pełna). */
export function zl(grosze: number): string {
  const neg = grosze < 0;
  const abs = Math.abs(Math.round(grosze));
  const whole = Math.floor(abs / 100);
  const cents = abs % 100;
  const w = String(whole).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  return (neg ? '−' : '') + w + (cents ? ',' + String(cents).padStart(2, '0') : '') + ' zł';
}

/** "49,99" / "49.99" / "49" → 4999. Zwraca null dla niepoprawnych danych. */
export function parseZl(input: string | null | undefined): number | null {
  if (input == null) return null;
  const s = String(input).trim().replace(/\s|zł/g, '').replace(',', '.');
  if (!/^\d+(\.\d{1,2})?$/.test(s)) return null;
  return Math.round(Number(s) * 100);
}
