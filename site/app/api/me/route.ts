import { NextResponse } from "next/server";
import { getActiveSubscription, getUserByTgId } from "@/lib/db";
import { getPanelSubscriptionUrl } from "@/lib/h1panel";
import { getSession } from "@/lib/telegram-auth";

export async function GET() {
  const session = await getSession();
  if (!session.tgId) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const user = await getUserByTgId(session.tgId);
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const subscription = await getActiveSubscription(user.id);
  const key =
    subscription && user.marzban_username
      ? await getPanelSubscriptionUrl(user.marzban_username).catch(() => null)
      : null;

  return NextResponse.json({
    tgId: user.tg_id,
    username: user.username,
    trialUsed: user.trial_used,
    subscription: subscription
      ? { planId: subscription.plan_id, expiresAt: subscription.expires_at }
      : null,
    key,
  });
}
