import { Scanner } from './Scanner';

/** Powłoka skanera — bez zapytań do bazy, żeby działała z cache service workera bez internetu. */
export default async function DoorPage({ params }: { params: Promise<{ eventId: string }> }) {
  const { eventId } = await params;
  return <Scanner eventId={eventId} />;
}
