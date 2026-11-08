import { NextRequest, NextResponse } from "next/server";
import { revokeAppToken } from "@/lib/app-auth";

export const dynamic = "force-dynamic";

// Выход из приложения Ygolek VPN: токен больше не действует.
export async function POST(request: NextRequest) {
  await revokeAppToken(request.headers.get("authorization"));
  return NextResponse.json({ ok: true });
}
