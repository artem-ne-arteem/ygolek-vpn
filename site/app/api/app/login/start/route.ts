import { NextRequest, NextResponse } from "next/server";
import { startAppLogin } from "@/lib/app-auth";

export const dynamic = "force-dynamic";

// Приложение Ygolek VPN начинает вход: получает ссылку на бота и секрет для опроса.
export async function POST(request: NextRequest) {
  const body = (await request.json().catch(() => ({}))) as { device?: unknown };
  const device = typeof body.device === "string" ? body.device : "";
  return NextResponse.json(await startAppLogin(device));
}
