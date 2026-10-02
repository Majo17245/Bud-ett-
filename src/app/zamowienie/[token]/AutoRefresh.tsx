'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/** Strona zamówienia odświeża się, dopóki operator nie potwierdzi płatności. */
export function AutoRefresh() {
  const router = useRouter();
  useEffect(() => {
    const t = setInterval(() => router.refresh(), 3000);
    return () => clearInterval(t);
  }, [router]);
  return null;
}
