import { Client } from 'pg';
import { migrate } from '../scripts/migrate';

export default async function setup() {
  const url = process.env.TEST_DATABASE_URL ?? 'postgres://app:app@localhost:5432/klub_test';
  const c = new Client({ connectionString: url });
  await c.connect();
  // Czysta baza dla każdego uruchomienia testów.
  await c.query('drop schema public cascade; create schema public;');
  await c.end();
  await migrate(url, () => {});
}
