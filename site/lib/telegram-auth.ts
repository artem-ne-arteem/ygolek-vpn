import crypto from "node:crypto";
import { cookies } from "next/headers";
import { getIronSession, type SessionOptions } from "iron-session";

export type TelegramAuthPayload = {
  id: number;
  first_name?: string;
  last_name?: string;
  username?: string;
  photo_url?: string;
  auth_date: number;
  hash: string;
};

const MAX_AUTH_AGE_SECONDS = 24 * 60 * 60;

/** Проверка подписи Telegram Login Widget — https://core.telegram.org/widgets/login#checking-authorization */
export function verifyTelegramAuth(payload: TelegramAuthPayload): boolean {
  const botToken = process.env.BOT_TOKEN;
  if (!botToken) throw new Error("BOT_TOKEN is not set");

  const { hash, ...rest } = payload;
  const dataCheckString = Object.keys(rest)
    .sort()
    .map((key) => `${key}=${(rest as Record<string, unknown>)[key]}`)
    .join("\n");

  const secretKey = crypto.createHash("sha256").update(botToken).digest();
  const computedHash = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");

  if (computedHash !== hash) return false;

  const ageSeconds = Date.now() / 1000 - payload.auth_date;
  return ageSeconds >= 0 && ageSeconds <= MAX_AUTH_AGE_SECONDS;
}

export type SessionData = {
  tgId?: number;
};

const sessionOptions: SessionOptions = {
  password: process.env.SESSION_SECRET ?? "dev-only-insecure-secret-change-me-32chars",
  cookieName: "ygolek_session",
  cookieOptions: {
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
  },
};

export async function getSession() {
  const cookieStore = cookies();
  return getIronSession<SessionData>(cookieStore, sessionOptions);
}
