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
export const PLANS: Plan[] = [
  {
    id: "1m",
    title: "1 месяц",
    days: 30,
    trafficGb: 200,
    trafficLabel: "200 ГБ",
    priceStars: 150,
    priceLabel: "150 ⭐ / мес",
  },
  {
    id: "3m",
    title: "3 месяца",
    days: 90,
    trafficGb: 600,
    trafficLabel: "600 ГБ",
    priceStars: 400,
    priceLabel: "400 ⭐",
    highlighted: true,
  },
  {
    id: "12m",
    title: "12 месяцев",
    days: 365,
    trafficGb: null,
    trafficLabel: "безлимит",
    priceStars: 1400,
    priceLabel: "1400 ⭐",
  },
];

export function getPlan(id: string): Plan | undefined {
  return PLANS.find((p) => p.id === id);
}

export const TRIAL_DAYS = 3;
export const TRIAL_TRAFFIC_GB = 5;

export const TRIAL = {
  days: TRIAL_DAYS,
  trafficLabel: `${TRIAL_TRAFFIC_GB} ГБ`,
};

export const BOT_USERNAME =
  process.env.NEXT_PUBLIC_BOT_USERNAME || "ygolek_vpn_bot";

export function botDeepLink(planId?: string) {
  const base = `https://t.me/${BOT_USERNAME}`;
  return planId ? `${base}?start=plan_${planId}` : base;
}
