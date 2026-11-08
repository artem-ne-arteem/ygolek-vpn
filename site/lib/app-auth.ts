// Вход в приложение Ygolek VPN через бота.
//
// 1. Приложение: POST /api/app/login/start → { code, secret, botUrl }
//    и показывает ссылку/QR t.me/<бот>?start=app_<code>.
// 2. Пользователь подтверждает вход в боте (bot/bot/handlers/applogin.py).
// 3. Приложение: POST /api/app/login/poll { code, secret } → { status: "ok", token }.
// 4. Дальше: GET /api/app/me с заголовком Authorization: Bearer <token>.
//
// Таблицу app_logins создаёт бот (bot/bot/db/models.py → AppLogin).
// В базе лежат только sha256 от секрета и токена.
import crypto from "node:crypto";
import { query, type DbUser } from "./db";
import { BOT_USERNAME } from "./plans";

export const LOGIN_TTL_MINUTES = 10;

export type AppLoginRow = {
  id: number;
  code: string;
  secret_hash: string;
  device: string;
  status: "pending" | "approved" | "issued" | "denied" | "revoked";
  user_id: number | null;
  token_hash: string | null;
  created_at: Date;
};

export function sha256(value: string): string {
  return crypto.createHash("sha256").update(value).digest("hex");
}

function randomToken(bytes: number): string {
  return crypto.randomBytes(bytes).toString("base64url");
}

function safeEqual(a: string, b: string): boolean {
  const x = Buffer.from(a);
  const y = Buffer.from(b);
  return x.length === y.length && crypto.timingSafeEqual(x, y);
}

export function botLoginUrl(code: string): string {
  return `https://t.me/${BOT_USERNAME}?start=app_${code}`;
}

export async function startAppLogin(device: string) {
  const code = randomToken(18); // 24 символа [A-Za-z0-9_-] — подходит для /start
  const secret = randomToken(32);
  const cleanDevice = device.replace(/[\u0000-\u001f]/g, "").trim().slice(0, 64) || "Ygolek VPN";

  // Заодно чистим старые неподтверждённые запросы
  await query(
    "DELETE FROM app_logins WHERE status IN ('pending', 'denied') AND created_at < now() - interval '1 day'"
  );
  await query(
    `INSERT INTO app_logins (code, secret_hash, device, status, created_at)
     VALUES ($1, $2, $3, 'pending', (now() AT TIME ZONE 'utc'))`,
    [code, sha256(secret), cleanDevice]
  );
  return { code, secret, botUrl: botLoginUrl(code), expiresIn: LOGIN_TTL_MINUTES * 60 };
}

export type PollResult =
  | { status: "pending" }
  | { status: "ok"; token: string }
  | { status: "denied" | "expired" | "invalid" };

export async function pollAppLogin(code: string, secret: string): Promise<PollResult> {
  const rows = await query<AppLoginRow & { expired: boolean }>(
    `SELECT *, created_at < (now() AT TIME ZONE 'utc') - ($2 || ' minutes')::interval AS expired
     FROM app_logins WHERE code = $1`,
    [code, LOGIN_TTL_MINUTES]
  );
  const login = rows[0];
  if (!login || !safeEqual(login.secret_hash, sha256(secret))) return { status: "invalid" };
  if (login.status === "denied") return { status: "denied" };
  if (login.status === "pending") return login.expired ? { status: "expired" } : { status: "pending" };
  if (login.status !== "approved" || !login.user_id) return { status: "invalid" };

  // Токен выдаётся один раз: approved → issued атомарно
  const token = randomToken(32);
  const updated = await query(
    `UPDATE app_logins SET status = 'issued', token_hash = $2, last_seen_at = (now() AT TIME ZONE 'utc')
     WHERE id = $1 AND status = 'approved' RETURNING id`,
    [login.id, sha256(token)]
  );
  return updated.length ? { status: "ok", token } : { status: "invalid" };
}

function bearer(header: string | null): string | null {
  const match = header?.match(/^Bearer\s+(\S+)$/i);
  return match ? match[1] : null;
}

/** Пользователь по токену приложения или null. */
export async function userFromAppToken(authorization: string | null): Promise<DbUser | null> {
  const token = bearer(authorization);
  if (!token) return null;
  const rows = await query<DbUser>(
    `UPDATE app_logins l SET last_seen_at = (now() AT TIME ZONE 'utc')
     FROM users u
     WHERE l.token_hash = $1 AND l.status = 'issued' AND u.id = l.user_id
     RETURNING u.*`,
    [sha256(token)]
  );
  return rows[0] ?? null;
}

export async function revokeAppToken(authorization: string | null): Promise<boolean> {
  const token = bearer(authorization);
  if (!token) return false;
  const rows = await query(
    "UPDATE app_logins SET status = 'revoked' WHERE token_hash = $1 AND status = 'issued' RETURNING id",
    [sha256(token)]
  );
  return rows.length > 0;
}
