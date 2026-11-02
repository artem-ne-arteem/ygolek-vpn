"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { TelegramLoginButton } from "./TelegramLoginButton";

export function HeaderAuth() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/me")
      .then((r) => setLoggedIn(r.ok))
      .catch(() => setLoggedIn(false));
  }, []);

  if (loggedIn === null) {
    return <div className="h-10 w-10" />;
  }

  if (loggedIn) {
    return (
      <Link
        href="/account"
        className="rounded-full border border-white/15 px-4 py-2 text-sm font-medium text-white hover:border-accent/60 hover:text-accent"
      >
        Личный кабинет
      </Link>
    );
  }

  return <TelegramLoginButton />;
}
