import { NextRequest, NextResponse } from "next/server";
import { getPlan } from "@/lib/plans";
import { getSession } from "@/lib/telegram-auth";

export async function POST(request: NextRequest) {
  const session = await getSession();
  if (!session.tgId) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const { planId } = (await request.json()) as { planId: string };
  const plan = getPlan(planId);
  if (!plan) {
    return NextResponse.json({ error: "unknown_plan" }, { status: 400 });
  }

  const botToken = process.env.BOT_TOKEN;
  if (!botToken) {
    return NextResponse.json({ error: "server_misconfigured" }, { status: 500 });
  }

  // Оплата всё так же идёт через Telegram Stars и обрабатывается ботом
  // (bot/bot/handlers/payment.py) — сайт только генерирует ссылку на инвойс,
  // а не запускает отдельный платёжный флоу.
  const resp = await fetch(`https://api.telegram.org/bot${botToken}/createInvoiceLink`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: `Ygolek VPN — ${plan.title}`,
      description: `Подписка на ${plan.title} (${plan.trafficLabel}, ${plan.days} дн.)`,
      payload: `plan:${plan.id}`,
      provider_token: "",
      currency: "XTR",
      prices: [{ label: plan.title, amount: plan.priceStars }],
    }),
  });

  const data = await resp.json();
  if (!data.ok) {
    return NextResponse.json({ error: "telegram_error", details: data }, { status: 502 });
  }

  return NextResponse.json({ url: data.result });
}
