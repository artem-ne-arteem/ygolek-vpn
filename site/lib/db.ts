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
  // докупленные устройства (колонки добавляет бот); до extra_devices_until
  extra_devices?: number | null;
  extra_devices_until?: Date | null;
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

// Заказы на оплату картой / СБП (таблица card_orders, её создаёт бот).
// Подписку по оплаченному заказу выдаёт бот (bot/bot/card_orders.py).
export async function createCardOrder(userId: number, planId: string, amountRub: number, source: string): Promise<number> {
  const rows = await query<{ id: number }>(
    `INSERT INTO card_orders (user_id, plan_id, amount_rub, status, source, fulfil_attempts, created_at)
     VALUES ($1, $2, $3, 'pending', $4, 0, now() AT TIME ZONE 'utc') RETURNING id`,
    [userId, planId, amountRub, source]
  );
  return rows[0].id;
}

export async function setCardOrderTransaction(orderId: number, transactionId: string | null): Promise<void> {
  if (transactionId) {
    await query("UPDATE card_orders SET transaction_id = $1 WHERE id = $2", [transactionId, orderId]);
  } else {
    await query("UPDATE card_orders SET status = 'canceled' WHERE id = $1", [orderId]);
  }
}

export type DbCardOrder = { id: number; amount_rub: number; status: string };

export async function getCardOrderByTransaction(transactionId: string): Promise<DbCardOrder | null> {
  const rows = await query<DbCardOrder>(
    "SELECT id, amount_rub, status FROM card_orders WHERE transaction_id = $1",
    [transactionId]
  );
  return rows[0] ?? null;
}

/** pending → paid / canceled. Повторные колбэки ничего не меняют. */
export async function settleCardOrder(orderId: number, status: "paid" | "canceled"): Promise<void> {
  if (status === "paid") {
    await query(
      "UPDATE card_orders SET status = 'paid', paid_at = now() AT TIME ZONE 'utc' WHERE id = $1 AND status = 'pending'",
      [orderId]
    );
  } else {
    await query("UPDATE card_orders SET status = 'canceled' WHERE id = $1 AND status = 'pending'", [orderId]);
  }
}
