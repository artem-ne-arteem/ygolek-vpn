import { NextRequest, NextResponse } from "next/server";
import { getActiveSubscription, getOrCreateUser } from "@/lib/db";
import { getPanelSubscriptionUrl } from "@/lib/h1panel";
import { verifyWebAppInitData } from "@/lib/webapp-auth";

export const dynamic = "force-dynamic";

// Данные для мини-аппа в Telegram. Авторизация — по initData из заголовка.
export async function GET(request: NextRequest) {
  const tgUser = verifyWebAppInitData(request.headers.get("x-telegram-init-data"));
  if (!tgUser) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const user = await getOrCreateUser(tgUser.id, tgUser.username);
  const subscription = await getActiveSubscription(user.id);
  const key =
    subscription && user.marzban_username
      ? await getPanelSubscriptionUrl(user.marzban_username).catch(() => null)
      : null;

  return NextResponse.json({
    firstName: tgUser.firstName,
    username: tgUser.username,
    subscription: subscription ? { expiresAt: subscription.expires_at } : null,
    key,
  });
}
