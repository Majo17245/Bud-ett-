import { applySync, SyncInput } from '@/lib/services/door';
import { authorizeDoor, noStore } from '../../auth';

export async function POST(req: Request, { params }: { params: Promise<{ eventId: string }> }) {
  const { eventId } = await params;
  if (!(await authorizeDoor(req, eventId))) return Response.json({ error: 'unauthorized' }, { status: 401, headers: noStore });
  const parsed = SyncInput.safeParse(await req.json().catch(() => null));
  if (!parsed.success) return Response.json({ error: 'bad_request' }, { status: 400, headers: noStore });
  return Response.json(await applySync(eventId, parsed.data), { headers: noStore });
}
