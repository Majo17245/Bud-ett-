function required(name: string): string {
  const v = process.env[name];
  if (!v) throw new Error(`Brak zmiennej środowiskowej ${name} (zob. .env.example)`);
  return v;
}

export const env = {
  get databaseUrl() {
    return required('DATABASE_URL');
  },
  get appUrl() {
    return (process.env.APP_URL ?? 'http://localhost:3000').replace(/\/$/, '');
  },
  get appSecret() {
    const s = required('APP_SECRET');
    if (s.length < 32) throw new Error('APP_SECRET musi mieć co najmniej 32 znaki');
    return s;
  },
  get allowMockPayments() {
    return process.env.ALLOW_MOCK_PAYMENTS === 'true';
  },
  get resendApiKey() {
    return process.env.RESEND_API_KEY || '';
  },
  get mailFrom() {
    return process.env.MAIL_FROM || 'Klubowy <bilety@example.com>';
  },
  get cronSecret() {
    return process.env.CRON_SECRET || '';
  },
};
