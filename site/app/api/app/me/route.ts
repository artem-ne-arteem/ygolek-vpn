import { NextRequest, NextResponse } from "next/server";
import { userFromAppToken } from "@/lib/app-auth";
import { getActiveSubscription } from "@/lib/db";
import { getPanelSubscriptionUrl } from "@/lib/h1panel";
import { botDeepLink, DEVICE_LIMIT } from "@/lib/plans";

export const dynamic = "force-dynamic";

// Аккаунт для приложения Ygolek VPN: подписка, ссылка на неё и лимит устройств.
export async function GET(request: NextRequest) {
  const user = await userFromAppToken(request.headers.get("authorization"));
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const subscription = await getActiveSubscription(user.id);
  const key =
    subscription && user.marzban_username
      ? await getPanelSubscriptionUrl(user.marzban_username).catch(() => null)
      : null;

  const extraActive =
    user.extra_devices_until && new Date(user.extra_devices_until).getTime() > Date.now()
      ? user.extra_devices ?? 0
      : 0;

  return NextResponse.json({
    tgId: Number(user.tg_id),
    username: user.username,
    deviceLimit: DEVICE_LIMIT + extraActive,
    subscription: subscription ? { planId: subscription.plan_id, expiresAt: subscription.expires_at } : null,
    key,
    renewUrl: botDeepLink("1m"),
    botUrl: botDeepLink(),
  });
}
