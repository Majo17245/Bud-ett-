import { Pool, type PoolClient, type QueryResultRow } from 'pg';
import { env } from './env';

export type Db = Pick<Pool, 'query'> | PoolClient;

const g = globalThis as unknown as { __pgPool?: Pool };

export function pool(): Pool {
  if (!g.__pgPool) {
    const ssl = process.env.DATABASE_SSL;
    g.__pgPool = new Pool({
      connectionString: env.databaseUrl,
      max: Number(process.env.DB_POOL_MAX ?? 5),
      // Supabase: połączenie szyfrowane; certyfikat poolera nie jest w publicznym łańcuchu zaufania.
      ssl: ssl === 'require' ? { rejectUnauthorized: false } : undefined,
      idleTimeoutMillis: 10_000,
    });
  }
  return g.__pgPool;
}

export async function q<T extends QueryResultRow>(sql: string, params: unknown[] = [], db: Db = pool()): Promise<T[]> {
  const res = await db.query<T>(sql, params as unknown[]);
  return res.rows;
}

export async function one<T extends QueryResultRow>(sql: string, params: unknown[] = [], db: Db = pool()): Promise<T | null> {
  const rows = await q<T>(sql, params, db);
  return rows[0] ?? null;
}

export async function tx<T>(fn: (c: PoolClient) => Promise<T>): Promise<T> {
  const client = await pool().connect();
  try {
    await client.query('begin');
    const out = await fn(client);
    await client.query('commit');
    return out;
  } catch (e) {
    await client.query('rollback').catch(() => {});
    throw e;
  } finally {
    client.release();
  }
}

/** Błąd biznesowy, którego treść można bezpiecznie pokazać użytkownikowi. */
export class UserError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'UserError';
  }
}
