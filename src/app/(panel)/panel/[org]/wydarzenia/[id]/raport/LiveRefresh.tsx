'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

/** Odświeża raport co kilka sekund, gdy karta jest widoczna. */
export function LiveRefresh({ seconds = 15 }: { seconds?: number }) {
  const router = useRouter();
  const [at, setAt] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => {
      if (document.visibilityState === 'visible') {
        router.refresh();
        setAt(new Date());
      }
    }, seconds * 1000);
    return () => clearInterval(t);
  }, [router, seconds]);
  return <span className="muted" style={{ fontSize: '.85rem' }}>● na żywo · odświeżono {at.toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>;
}
