import { buildManifest } from '@/lib/services/door';
import { authorizeDoor, noStore } from '../../auth';

export async function GET(req: Request, { params }: { params: Promise<{ eventId: string }> }) {
  const { eventId } = await params;
  if (!(await authorizeDoor(req, eventId))) return Response.json({ error: 'unauthorized' }, { status: 401, headers: noStore });
  const manifest = await buildManifest(eventId);
  if (!manifest) return Response.json({ error: 'not_found' }, { status: 404, headers: noStore });
  return Response.json(manifest, { headers: noStore });
}
