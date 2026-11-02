import { NextRequest, NextResponse } from "next/server";
import { getOrCreateUser } from "@/lib/db";
import { getSession, verifyTelegramAuth, type TelegramAuthPayload } from "@/lib/telegram-auth";

export async function POST(request: NextRequest) {
  const payload = (await request.json()) as TelegramAuthPayload;

  if (!verifyTelegramAuth(payload)) {
    return NextResponse.json({ error: "invalid_signature" }, { status: 401 });
  }

  await getOrCreateUser(payload.id, payload.username ?? null);

  const session = await getSession();
  session.tgId = payload.id;
  await session.save();

  return NextResponse.json({ ok: true });
}
