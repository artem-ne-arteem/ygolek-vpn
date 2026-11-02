import crypto from "node:crypto";

// Проверка initData мини-аппа Telegram:
// https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
// Отличается от Login Widget (lib/telegram-auth.ts): секрет — HMAC("WebAppData", токен бота).

const MAX_AGE_SECONDS = 24 * 60 * 60;

export type WebAppUser = { id: number; username: string | null; firstName: string | null };

export function verifyWebAppInitData(initData: string | null): WebAppUser | null {
  const botToken = process.env.BOT_TOKEN;
  if (!botToken || !initData) return null;

  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  if (!hash) return null;
  params.delete("hash");

  const dataCheckString = [...params.entries()]
    .map(([key, value]) => `${key}=${value}`)
    .sort()
    .join("\n");

  const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const computed = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");

  const a = Buffer.from(computed, "hex");
  const b = Buffer.from(hash, "hex");
  if (a.length !== b.length || !crypto.timingSafeEqual(a, b)) return null;

  const authDate = Number(params.get("auth_date"));
  const age = Date.now() / 1000 - authDate;
  if (!authDate || age < 0 || age > MAX_AGE_SECONDS) return null;

  try {
    const user = JSON.parse(params.get("user") ?? "null");
    if (!user?.id) return null;
    return { id: user.id, username: user.username ?? null, firstName: user.first_name ?? null };
  } catch {
    return null;
  }
}
