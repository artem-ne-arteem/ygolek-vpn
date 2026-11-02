"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Icon } from "./Icon";
import { TelegramLoginButton } from "./TelegramLoginButton";

export function HeaderAuth() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null);

  useEffect(() => {
    fetch("/api/me")
      .then((r) => setLoggedIn(r.ok))
      .catch(() => setLoggedIn(false));
  }, []);

  if (loggedIn === null) {
    return <div className="h-10 w-28" />;
  }

  if (loggedIn) {
    return (
      <Link href="/account" className="btn-primary px-4 py-2">
        <Icon name="user" className="h-4 w-4" />
        Кабинет
      </Link>
    );
  }

  return <TelegramLoginButton />;
}
