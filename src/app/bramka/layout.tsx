import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Bramka',
  manifest: '/manifest.webmanifest',
  robots: { index: false },
  appleWebApp: { capable: true, title: 'Bramka', statusBarStyle: 'black-translucent' },
};

export default function DoorLayout({ children }: { children: React.ReactNode }) {
  return children;
}
