import { Pool, type QueryResultRow } from "pg";

// Та же Postgres-база, что использует бот (bot/bot/db/models.py) — сайт
// только читает/пишет в существующие таблицы, схему создаёт бот через
// SQLAlchemy при старте.
const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: { rejectUnauthorized: false },
  max: 3,
});

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  params: unknown[] = []
): Promise<T[]> {
  const result = await pool.query<T>(text, params);
  return result.rows;
}

export type DbUser = {
  id: number;
  tg_id: string;
  username: string | null;
  marzban_username: string | null;
  trial_used: boolean;
};

export type DbSubscription = {
  id: number;
  user_id: number;
  plan_id: string;
  expires_at: Date;
};

export async function getUserByTgId(tgId: number): Promise<DbUser | null> {
  const rows = await query<DbUser>("SELECT * FROM users WHERE tg_id = $1", [tgId]);
  return rows[0] ?? null;
}

export async function getOrCreateUser(tgId: number, username: string | null): Promise<DbUser> {
  const existing = await query<DbUser>("SELECT * FROM users WHERE tg_id = $1", [tgId]);
  if (existing[0]) return existing[0];

  const created = await query<DbUser>(
    "INSERT INTO users (tg_id, username, trial_used, created_at) VALUES ($1, $2, false, now()) RETURNING *",
    [tgId, username]
  );
  return created[0];
}

export async function getActiveSubscription(userId: number): Promise<DbSubscription | null> {
  const rows = await query<DbSubscription>(
    "SELECT * FROM subscriptions WHERE user_id = $1 AND expires_at > now() ORDER BY expires_at DESC LIMIT 1",
    [userId]
  );
  return rows[0] ?? null;
}

export async function recordTrialSubscription(userId: number, days: number): Promise<DbSubscription> {
  const rows = await query<DbSubscription>(
    `INSERT INTO subscriptions (user_id, plan_id, expires_at, reminder_sent, created_at)
     VALUES ($1, 'trial', now() + ($2 || ' days')::interval, false, now())
     RETURNING *`,
    [userId, days]
  );
  await query("UPDATE users SET trial_used = true WHERE id = $1", [userId]);
  return rows[0];
}

export async function setMarzbanUsername(userId: number, marzbanUsername: string): Promise<void> {
  await query("UPDATE users SET marzban_username = $1 WHERE id = $2", [marzbanUsername, userId]);
}
