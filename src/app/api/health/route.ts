import { one } from '@/lib/db';

export async function GET() {
  try {
    await one('select 1');
    return Response.json({ ok: true, db: true, at: new Date().toISOString() }, { headers: { 'Cache-Control': 'no-store' } });
  } catch {
    return Response.json({ ok: false, db: false }, { status: 503, headers: { 'Cache-Control': 'no-store' } });
  }
}
