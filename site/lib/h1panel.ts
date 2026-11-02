// Клиент к API панели H1 (h1cloud) — то же, что bot/bot/h1panel/client.py.
// https://my.h1cloud.net/api-docs#h1-panel-api
import { DEVICE_LIMIT } from "./plans";

const MOCK = process.env.H1_PANEL_MOCK !== "false";
const API_URL = (process.env.H1_PANEL_URL ?? "").replace(/\/+$/, "");
const TOKEN = process.env.H1_PANEL_TOKEN ?? "";

type H1Client = {
  subscription_url?: string;
  sub_url?: string;
};

function mockUrl(username: string) {
  return `https://example.invalid/sub/${username}/mock-h1-config`;
}

function subUrl(client: H1Client): string | null {
  return client.subscription_url || client.sub_url || null;
}

async function request(method: string, path: string, body?: unknown): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    method,
    headers: { Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
    cache: "no-store",
  });
}

async function unwrap(resp: Response): Promise<H1Client> {
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok || data.ok === false) {
    throw new Error(`H1 panel ${resp.status}: ${data.error ?? "unknown error"}`);
  }
  return data.client ?? data;
}

async function getClient(username: string): Promise<H1Client | null> {
  const resp = await request("GET", `/api/clients/${encodeURIComponent(username)}`);
  if (resp.status === 404) return null;
  return unwrap(resp);
}

/** Создаёт клиента или продлевает существующего; возвращает ссылку подписки. */
export async function upsertPanelUser(
  username: string,
  days: number,
  trafficGb: number | null
): Promise<string> {
  if (MOCK) return mockUrl(username);

  const traffic_limit_gb = trafficGb ?? 0; // 0 в панели = безлимит
  const existing = await getClient(username);
  const client = existing
    ? await unwrap(
        await request("PATCH", `/api/clients/${encodeURIComponent(username)}`, {
          days,
          traffic_limit_gb,
          device_limit: DEVICE_LIMIT,
        })
      )
    : await unwrap(
        await request("POST", "/api/create", {
          name: username,
          uuid: crypto.randomUUID(),
          days,
          traffic_limit_gb,
          device_limit: DEVICE_LIMIT,
        })
      );

  const url = subUrl(client) ?? subUrl((await getClient(username)) ?? {});
  if (!url) throw new Error(`H1 panel returned no subscription link for ${username}`);
  return url;
}

export async function getPanelSubscriptionUrl(username: string): Promise<string | null> {
  if (MOCK) return mockUrl(username);
  const client = await getClient(username);
  return client ? subUrl(client) : null;
}
