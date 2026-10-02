import { env } from './env';

export type Mail = { to: string; subject: string; text: string; html?: string };

/** E-maile transakcyjne przez Resend; bez klucza API trafiają do logów (tryb deweloperski). */
export async function sendMail(mail: Mail): Promise<void> {
  if (!env.resendApiKey) {
    console.info(`[mail] do: ${mail.to} | ${mail.subject}\n${mail.text}`);
    return;
  }
  try {
    const res = await fetch('https://api.resend.com/emails', {
      method: 'POST',
      headers: { Authorization: `Bearer ${env.resendApiKey}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ from: env.mailFrom, to: [mail.to], subject: mail.subject, text: mail.text, html: mail.html }),
    });
    if (!res.ok) console.error('[mail] błąd wysyłki', res.status, await res.text());
  } catch (e) {
    // E-mail nie może zablokować zamówienia — bilety są zawsze dostępne pod linkiem zamówienia.
    console.error('[mail] błąd wysyłki', e);
  }
}
