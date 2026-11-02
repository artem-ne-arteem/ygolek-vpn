import { NextResponse } from "next/server";
import { getActiveSubscription, getUserByTgId } from "@/lib/db";
import { getMarzbanSubscriptionUrl } from "@/lib/marzban";
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
      ? await getMarzbanSubscriptionUrl(user.marzban_username)
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
