import type { Metadata, Viewport } from 'next';
import './globals.css';

// Wszystko renderujemy na żądanie: dostępność biletów i stan bramki nie mogą pochodzić z cache.
export const dynamic = 'force-dynamic';

export const metadata: Metadata = {
  title: { default: 'Klubowy — cały klub w jednym systemie', template: '%s · Klubowy' },
  description: 'Bilety, loże z przedpłatą, listy gości, promotorzy i bramka offline. Od DM do bramki.',
};

export const viewport: Viewport = { themeColor: '#0f1012', width: 'device-width', initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body>{children}</body>
    </html>
  );
}
