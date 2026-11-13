import { NextRequest, NextResponse } from "next/server";
import { getCardOrderByTransaction, settleCardOrder } from "@/lib/db";
import { getTransaction, isPlategaCallback } from "@/lib/platega";

// Колбэк Platega о смене статуса платежа. Адрес задаётся в кабинете Platega:
// Настройки → Callback URLs → https://<сайт>/api/platega/callback
// Здесь заказ только помечается оплаченным — подписку и ключ выдаёт бот
// (bot/bot/card_orders.py), он проверяет card_orders каждые 15 секунд.
export async function POST(request: NextRequest) {
  if (!isPlategaCallback(request.headers)) {
    return NextResponse.json({ error: "forbidden" }, { status: 403 });
  }

  const body = (await request.json().catch(() => null)) as { id?: string; status?: string } | null;
  if (!body?.id || !body.status) {
    return NextResponse.json({ error: "bad_request" }, { status: 400 });
  }

  const order = await getCardOrderByTransaction(body.id);
  if (!order) {
    // не наш платёж (или создан не через card_orders) — подтверждаем приём, чтобы не было повторов
    return NextResponse.json({ ok: true });
  }

  if (body.status === "CONFIRMED") {
    // Не верим телу колбэка на слово: сверяем статус и сумму через API Platega
    const tx = await getTransaction(body.id);
    const amount = Number(tx.paymentDetails?.amount ?? 0);
    if (tx.status === "CONFIRMED" && amount + 0.01 >= order.amount_rub) {
      await settleCardOrder(order.id, "paid");
    } else {
      console.error("Platega callback CONFIRMED not confirmed by API", { order: order.id, status: tx.status, amount });
    }
  } else if (body.status === "CANCELED") {
    await settleCardOrder(order.id, "canceled");
  } else {
    // CHARGEBACKED / DISPUTED / PARTIALLY_REFUNDED по уже выданной подписке — разбираем вручную
    console.warn("Platega callback status", { order: order.id, status: body.status });
  }

  return NextResponse.json({ ok: true });
}
