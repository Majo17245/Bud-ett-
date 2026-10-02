import { createCipheriv, createDecipheriv, createHash, randomBytes, scrypt as scryptCb, timingSafeEqual } from 'node:crypto';
import { promisify } from 'node:util';
import { env } from './env';

const scrypt = promisify(scryptCb) as (pw: string, salt: Buffer, len: number, opts: object) => Promise<Buffer>;

// Alfabet Crockforda: bez I, L, O, U — kody łatwo przeczytać na głos przy bramce.
const ALPHABET = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';

export function randomCode(length: number): string {
  const bytes = randomBytes(length);
  let out = '';
  for (const b of bytes) out += ALPHABET[b & 31];
  return out;
}

export type CodeKind = 'T' | 'G' | 'L';

/** Kod na bilet / zaproszenie / lożę: prefiks rodzaju + 11 znaków (55 bitów losowości). */
export function newEntryCode(kind: CodeKind): string {
  return kind + randomCode(11);
}

export function randomToken(bytes = 24): string {
  return randomBytes(bytes).toString('base64url');
}

export function sha256(s: string): string {
  return createHash('sha256').update(s).digest('hex');
}

export function sha384(s: string): string {
  return createHash('sha384').update(s).digest('hex');
}

const SCRYPT = { N: 16384, r: 8, p: 1 };

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16);
  const hash = await scrypt(password, salt, 32, SCRYPT);
  return `scrypt$${SCRYPT.N}$${salt.toString('base64url')}$${hash.toString('base64url')}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const [alg, n, saltB64, hashB64] = stored.split('$');
  if (alg !== 'scrypt' || !saltB64 || !hashB64) return false;
  const expected = Buffer.from(hashB64, 'base64url');
  const actual = await scrypt(password, Buffer.from(saltB64, 'base64url'), expected.length, { ...SCRYPT, N: Number(n) });
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}

function secretKey(): Buffer {
  return createHash('sha256').update('secrets-v1:' + env.appSecret).digest();
}

/** Szyfrowanie danych dostępowych operatora płatności (AES-256-GCM). */
export function encryptSecret(plain: string): string {
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', secretKey(), iv);
  const ct = Buffer.concat([cipher.update(plain, 'utf8'), cipher.final()]);
  return ['v1', iv.toString('base64url'), cipher.getAuthTag().toString('base64url'), ct.toString('base64url')].join(':');
}

export function decryptSecret(enc: string): string {
  const [v, iv, tag, ct] = enc.split(':');
  if (v !== 'v1' || !iv || !tag || !ct) throw new Error('Nieprawidłowy format zaszyfrowanej wartości');
  const decipher = createDecipheriv('aes-256-gcm', secretKey(), Buffer.from(iv, 'base64url'));
  decipher.setAuthTag(Buffer.from(tag, 'base64url'));
  return Buffer.concat([decipher.update(Buffer.from(ct, 'base64url')), decipher.final()]).toString('utf8');
}

/**
 * Klucz do wykrywania duplikatów na listach: bez wielkości liter, polskich znaków
 * i kolejności członów ("Kowalski Jan" == "jan kowalski").
 */
export function nameKey(name: string): string {
  return name
    .toLowerCase()
    .replace(/ł/g, 'l')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9 ]+/g, ' ')
    .split(/\s+/)
    .filter(Boolean)
    .sort()
    .join(' ');
}

export function normalizePhone(phone: string | null | undefined): string | null {
  if (!phone) return null;
  let d = phone.replace(/\D/g, '');
  if (d.startsWith('00')) d = d.slice(2);
  if (d.length === 9) d = '48' + d;
  return d.length >= 9 ? '+' + d : null;
}
