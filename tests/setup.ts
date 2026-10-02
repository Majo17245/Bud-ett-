process.env.DATABASE_URL = process.env.TEST_DATABASE_URL ?? 'postgres://app:app@localhost:5432/klub_test';
process.env.APP_SECRET = process.env.APP_SECRET ?? 'test-secret-test-secret-test-secret-1234';
process.env.ALLOW_MOCK_PAYMENTS = 'true';
process.env.APP_URL = 'http://localhost:3000';
