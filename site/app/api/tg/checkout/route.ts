import { NextRequest, NextResponse } from "next/server";
import { DEVICE_LIMIT, PLANS } from "@/lib/plans";
import { verifyWebAppInitData } from "@/lib/webapp-auth";

// Счёт в Telegram Stars для мини-аппа. Оплату, как и в остальных местах,
// принимает бот (bot/bot/handlers/payment.py) по payload "plan:<id>".
export async function POST(request: NextRequest) {
  const tgUser = verifyWebAppInitData(request.headers.get("x-telegram-init-data"));
  if (!tgUser) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const plan = PLANS[0];
  const botToken = process.env.BOT_TOKEN;
  if (!botToken) {
    return NextResponse.json({ error: "server_misconfigured" }, { status: 500 });
  }

  // Тексты — как в боте (без слова «VPN»), счёт показывается внутри Telegram
  const resp = await fetch(`https://api.telegram.org/bot${botToken}/createInvoiceLink`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: `Ygolek — ${plan.title}`,
      description: `Подписка на ${plan.title}: безлимит трафика, до ${DEVICE_LIMIT} устройств, ${plan.days} дн.`,
      payload: `plan:${plan.id}`,
      provider_token: "",
      currency: "XTR",
      prices: [{ label: plan.title, amount: plan.priceStars }],
    }),
  });

  const data = await resp.json();
  if (!data.ok) {
    return NextResponse.json({ error: "telegram_error" }, { status: 502 });
  }
  return NextResponse.json({ url: data.result });
}
