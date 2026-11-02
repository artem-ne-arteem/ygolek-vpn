import { NextResponse } from "next/server";
import { getUserByTgId, recordTrialSubscription, setMarzbanUsername } from "@/lib/db";
import { upsertPanelUser } from "@/lib/h1panel";
import { getSession } from "@/lib/telegram-auth";
import { TRIAL, TRIAL_DAYS, TRIAL_TRAFFIC_GB } from "@/lib/plans";

export async function POST() {
  if (!TRIAL.enabled) {
    return NextResponse.json({ error: "trial_disabled" }, { status: 403 });
  }

  const session = await getSession();
  if (!session.tgId) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  const user = await getUserByTgId(session.tgId);
  if (!user) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }

  if (user.trial_used) {
    return NextResponse.json({ error: "trial_already_used" }, { status: 400 });
  }

  const marzbanUsername = user.marzban_username ?? `tg${user.tg_id}`;

  let key: string;
  try {
    key = await upsertPanelUser(marzbanUsername, TRIAL_DAYS, TRIAL_TRAFFIC_GB);
  } catch {
    return NextResponse.json({ error: "marzban_unavailable" }, { status: 502 });
  }

  await setMarzbanUsername(user.id, marzbanUsername);
  const subscription = await recordTrialSubscription(user.id, TRIAL_DAYS);

  return NextResponse.json({ key, expiresAt: subscription.expires_at });
}
