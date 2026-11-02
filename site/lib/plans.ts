export type Plan = {
  id: string;
  title: string;
  days: number;
  trafficGb: number | null; // null = безлимит
  trafficLabel: string;
  priceStars: number;
  priceLabel: string;
  highlighted?: boolean;
};

// Держи в синхроне с bot/bot/plans.py — покупка происходит и в боте, и
// с сайта (через checkout, который тоже платит Stars), поэтому цены и
// объёмы трафика должны совпадать 1:1.
export const DEVICE_LIMIT = 5;

export const PLANS: Plan[] = [
  {
    id: "1m",
    title: "1 месяц",
    days: 30,
    trafficGb: null,
    trafficLabel: `безлимит · до ${DEVICE_LIMIT} устройств`,
    priceStars: 100,
    priceLabel: "100 ⭐ / мес",
  },
];

export function getPlan(id: string): Plan | undefined {
  return PLANS.find((p) => p.id === id);
}

export const TRIAL_DAYS = 3;
export const TRIAL_TRAFFIC_GB = 5;

export const TRIAL = {
  // Пробный период временно выключен (как и TRIAL_ENABLED в bot/bot/plans.py)
  enabled: false,
  days: TRIAL_DAYS,
  trafficLabel: `${TRIAL_TRAFFIC_GB} ГБ`,
};

export const BOT_USERNAME =
  process.env.NEXT_PUBLIC_BOT_USERNAME || "ygolek_vpn_bot";

export function botDeepLink(planId?: string) {
  const base = `https://t.me/${BOT_USERNAME}`;
  return planId ? `${base}?start=plan_${planId}` : base;
}
