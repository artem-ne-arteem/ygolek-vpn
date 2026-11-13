import { NextRequest, NextResponse } from "next/server";
import { createCardOrder, getOrCreateUser, setCardOrderTransaction } from "@/lib/db";
import { createPayment, plategaEnabled } from "@/lib/platega";
import { BOT_USERNAME, PLANS } from "@/lib/plans";
import { getSession } from "@/lib/telegram-auth";
import { verifyWebAppInitData } from "@/lib/webapp-auth";

// Ссылка на оплату картой / СБП (Platega) — для сайта и мини-аппа.
// Мини-апп авторизуется initData в заголовке, сайт — cookie-сессией.
export async function POST(request: NextRequest) {
  if (!plategaEnabled()) {
    return NextResponse.json({ error: "card_payment_disabled" }, { status: 503 });
  }

  const webAppUser = verifyWebAppInitData(request.headers.get("x-telegram-init-data"));
  let tgId: number | undefined = webAppUser?.id;
  let username: string | null = webAppUser?.username ?? null;
  if (!tgId) {
    const session = await getSession();
    tgId = session.tgId;
  }
  if (!tgId) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const plan = PLANS[0];
  const user = await getOrCreateUser(tgId, username);
  username = username ?? user.username;
  const source = webAppUser ? "miniapp" : "site";
  const orderId = await createCardOrder(user.id, plan.id, plan.priceRub, source);

  const returnUrl = webAppUser ? `https://t.me/${BOT_USERNAME}` : `${request.nextUrl.origin}/account`;
  try {
    const payment = await createPayment({
      amountRub: plan.priceRub,
      description: `Подписка Ygolek на ${plan.title}`,
      orderId,
      tgId,
      username,
      returnUrl,
    });
    await setCardOrderTransaction(orderId, payment.transactionId);
    return NextResponse.json({ url: payment.url });
  } catch (error) {
    console.error("Platega create payment failed", error);
    await setCardOrderTransaction(orderId, null);
    return NextResponse.json({ error: "payment_provider_error" }, { status: 502 });
  }
}
