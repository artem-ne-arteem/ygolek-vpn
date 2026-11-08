import { NextRequest, NextResponse } from "next/server";
import { pollAppLogin } from "@/lib/app-auth";

export const dynamic = "force-dynamic";

// Приложение ждёт подтверждения в боте. Ответы:
// pending — ещё не подтвердили; ok + token — вход выполнен (токен выдаётся один раз);
// denied — отменили в боте; expired — истекло время; invalid — неверный код/секрет.
export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => ({}))) as { code?: unknown; secret?: unknown };
  if (typeof body.code !== "string" || typeof body.secret !== "string") {
    return NextResponse.json({ status: "invalid" }, { status: 400 });
  }
  const result = await pollAppLogin(body.code, body.secret);
  return NextResponse.json(result, { status: result.status === "invalid" ? 404 : 200 });
}
