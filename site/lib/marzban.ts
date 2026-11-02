// TS-порт bot/bot/marzban/client.py — тот же mock-режим (MARZBAN_MOCK=true),
// чтобы личный кабинет работал уже сейчас, без поднятой VPN-ноды.

const MOCK = process.env.MARZBAN_MOCK !== "false";
const API_URL = process.env.MARZBAN_API_URL ?? "";
const ADMIN_USERNAME = process.env.MARZBAN_ADMIN_USERNAME ?? "";
const ADMIN_PASSWORD = process.env.MARZBAN_ADMIN_PASSWORD ?? "";
const SUB_DOMAIN = process.env.MARZBAN_SUB_DOMAIN ?? "";

let cachedToken: string | null = null;

function mockSubscriptionUrl(marzbanUsername: string): string {
  return `https://sub.ygolek-vpn.online/sub/${marzbanUsername}/mock-vless-config`;
}

async function ensureToken(): Promise<string> {
  if (cachedToken) return cachedToken;

  const resp = await fetch(`${API_URL}/api/admin/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: ADMIN_USERNAME, password: ADMIN_PASSWORD }),
  });
  if (!resp.ok) throw new Error(`Marzban auth failed: ${resp.status}`);
  const data = await resp.json();
  cachedToken = data.access_token;
  return cachedToken!;
}

async function marzbanRequest(method: string, path: string, body?: unknown): Promise<any> {
  let token = await ensureToken();
  let resp = await fetch(`${API_URL}${path}`, {
    method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (resp.status === 401) {
    cachedToken = null;
    token = await ensureToken();
    resp = await fetch(`${API_URL}${path}`, {
      method,
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  if (!resp.ok) throw new Error(`Marzban request failed: ${resp.status}`);
  return resp.json();
}

function resolveSubscriptionUrl(raw: string): string {
  if (raw.startsWith("/")) return `https://${SUB_DOMAIN.replace(/\/$/, "")}${raw}`;
  return raw;
}

export async function upsertMarzbanUser(
  marzbanUsername: string,
  days: number,
  trafficGb: number | null
): Promise<string> {
  if (MOCK) return mockSubscriptionUrl(marzbanUsername);

  const expire = Math.floor(Date.now() / 1000) + days * 24 * 60 * 60;
  const dataLimit = trafficGb === null ? null : trafficGb * 1024 * 1024 * 1024;

  let existing: any = null;
  try {
    existing = await marzbanRequest("GET", `/api/user/${marzbanUsername}`);
  } catch {
    existing = null;
  }

  const payload: Record<string, unknown> = {
    username: marzbanUsername,
    expire,
    data_limit: dataLimit,
    status: "active",
  };

  let result;
  if (existing === null) {
    payload.proxies = { vless: { flow: "xtls-rprx-vision" } };
    payload.inbounds = { vless: ["VLESS TCP REALITY"] };
    result = await marzbanRequest("POST", "/api/user", payload);
  } else {
    result = await marzbanRequest("PUT", `/api/user/${marzbanUsername}`, payload);
  }

  if (!result.subscription_url) throw new Error("Marzban did not return subscription_url");
  return resolveSubscriptionUrl(result.subscription_url);
}

export async function getMarzbanSubscriptionUrl(marzbanUsername: string): Promise<string | null> {
  if (MOCK) return mockSubscriptionUrl(marzbanUsername);

  try {
    const existing = await marzbanRequest("GET", `/api/user/${marzbanUsername}`);
    if (!existing?.subscription_url) return null;
    return resolveSubscriptionUrl(existing.subscription_url);
  } catch {
    return null;
  }
}
