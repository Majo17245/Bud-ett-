/**
 * Stosuje migracje z db/migrations w kolejności nazw. Każda migracja w osobnej transakcji.
 * Użycie: DATABASE_URL=... npm run db:migrate
 */
import { readdirSync, readFileSync } from 'node:fs';
import path from 'node:path';
import { Client } from 'pg';

export async function migrate(databaseUrl: string, log = console.log) {
  const client = new Client({
    connectionString: databaseUrl,
    ssl: process.env.DATABASE_SSL === 'require' ? { rejectUnauthorized: false } : undefined,
  });
  await client.connect();
  try {
    await client.query('create table if not exists schema_migrations (name text primary key, applied_at timestamptz not null default now())');
    // Blokada, żeby dwa równoległe wdrożenia nie stosowały migracji naraz.
    await client.query('select pg_advisory_lock(7243001)');
    const dir = path.join(process.cwd(), 'db', 'migrations');
    const files = readdirSync(dir).filter((f) => f.endsWith('.sql')).sort();
    const done = new Set((await client.query<{ name: string }>('select name from schema_migrations')).rows.map((r) => r.name));
    for (const f of files) {
      if (done.has(f)) continue;
      log(`→ ${f}`);
      await client.query('begin');
      try {
        await client.query(readFileSync(path.join(dir, f), 'utf8'));
        await client.query('insert into schema_migrations (name) values ($1)', [f]);
        await client.query('commit');
      } catch (e) {
        await client.query('rollback');
        throw e;
      }
    }
    log('Migracje aktualne.');
  } finally {
    await client.query('select pg_advisory_unlock(7243001)').catch(() => {});
    await client.end();
  }
}

if (typeof require !== 'undefined' && require.main === module) {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('Ustaw DATABASE_URL');
    process.exit(1);
  }
  migrate(url).catch((e) => {
    console.error(e);
    process.exit(1);
  });
}
