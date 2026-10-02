import QRCode from 'qrcode';

/** Kod QR jako SVG renderowany na serwerze (bez JS po stronie gościa). */
export async function Qr({ value, label }: { value: string; label?: string }) {
  const svg = await QRCode.toString(value, { type: 'svg', errorCorrectionLevel: 'M', margin: 1, color: { dark: '#000000', light: '#ffffff' } });
  return <div role="img" aria-label={label ?? `Kod QR ${value}`} dangerouslySetInnerHTML={{ __html: svg }} />;
}
