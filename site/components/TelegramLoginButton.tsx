"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { BOT_USERNAME } from "@/lib/plans";

declare global {
  interface Window {
    onTelegramAuth?: (user: Record<string, unknown>) => void;
  }
}

export function TelegramLoginButton() {
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    window.onTelegramAuth = async (user) => {
      const resp = await fetch("/api/auth/telegram", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(user),
      });
      if (resp.ok) {
        router.push("/account");
        router.refresh();
      }
    };

    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", BOT_USERNAME);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-radius", "999");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");

    containerRef.current?.appendChild(script);

    return () => {
      delete window.onTelegramAuth;
    };
  }, [router]);

  return <div ref={containerRef} />;
}
