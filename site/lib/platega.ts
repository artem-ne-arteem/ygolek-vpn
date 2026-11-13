import crypto from "node:crypto";

// Клиент Platega (оплата картой / СБП) — https://docs.platega.io/
// Тот же контракт, что и в боте (bot/bot/payments/platega.py): payload
// "order:<id>" указывает на строку card_orders. Подписку выдаёт бот.

const API_URL = "https://app.platega.io";

function credentials() {
  const merchantId = process.env.PLATEGA_MERCHANT_ID?.trim() ?? "";
  const secret = process.env.PLATEGA_SECRET?.trim() ?? "";
  return { merchantId, secret };
}

export function plategaEnabled(): boolean {
  const { merchantId, secret } = credentials();
  return Boolean(merchantId && secret);
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const { merchantId, secret } = credentials();
  const resp = await fetch(`${API_URL}${path}`, {
    method,
    headers: { "X-MerchantId": merchantId, "X-Secret": secret, "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    throw new Error(`Platega ${method} ${path} -> ${resp.status}: ${data?.message ?? ""} (traceId=${data?.traceId ?? ""})`);
  }
  return data as T;
}

export async function createPayment(params: {
  amountRub: number;
  description: string;
  orderId: number;
  tgId: number;
  username: string | null;
  returnUrl: string;
}): Promise<{ transactionId: string; url: string }> {
  const metadata: Record<string, string> = {
    // стабильный email покупателя в формате из документации Platega
    user_email: `${params.tgId}@telegram.org`,
    userId: String(params.tgId),
  };
  if (params.username) metadata.userName = `@${params.username}`;

  const data = await request<{ transactionId?: string; url?: string; redirect?: string }>(
    "POST",
    "/v2/transaction/process",
    {
      paymentDetails: { amount: params.amountRub, currency: "RUB" },
      description: params.description,
      return: params.returnUrl,
      failedUrl: params.returnUrl,
      payload: `order:${params.orderId}`,
      orderId: String(params.orderId),
      metadata,
    }
  );
  const url = data.url ?? data.redirect;
  if (!data.transactionId || !url) throw new Error("Platega не вернула ссылку на оплату");
  return { transactionId: data.transactionId, url };
}

export type PlategaTransaction = {
  id: string;
  status: string;
  paymentDetails?: { amount?: number; currency?: string };
  payload?: string;
};

export function getTransaction(id: string): Promise<PlategaTransaction> {
  return request<PlategaTransaction>("GET", `/transaction/${encodeURIComponent(id)}`);
}

function safeEqual(a: string, b: string): boolean {
  const x = Buffer.from(a);
  const y = Buffer.from(b);
  return x.length === y.length && crypto.timingSafeEqual(x, y);
}

/** Колбэк Platega подписан теми же X-MerchantId / X-Secret, что и наши запросы. */
export function isPlategaCallback(headers: Headers): boolean {
  const { merchantId, secret } = credentials();
  if (!merchantId || !secret) return false;
  return (
    safeEqual(headers.get("x-merchantid")?.trim() ?? "", merchantId) &&
    safeEqual(headers.get("x-secret")?.trim() ?? "", secret)
  );
}
