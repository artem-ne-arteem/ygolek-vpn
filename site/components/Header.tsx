"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { botDeepLink } from "@/lib/plans";
import { HeaderAuth } from "./HeaderAuth";

export function Header() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={`sticky top-0 z-50 flex items-center justify-between px-6 py-4 transition-colors duration-300 md:px-12 ${
        scrolled ? "border-b border-white/10 bg-ink/80 backdrop-blur-md" : "border-b border-transparent"
      }`}
    >
      <Link href="/" className="flex items-center gap-3 text-lg font-semibold">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/logo.jpg"
          alt="Ygolek VPN"
          className="logo-pulse h-9 w-9 scale-125 rounded-full bg-[#f5f0ec] object-cover"
        />
        Ygolek VPN
      </Link>
      <nav className="flex items-center gap-5 text-sm text-white/70">
        <Link href="/faq" className="hidden hover:text-white sm:inline">
          Как подключить
        </Link>
        <a href={botDeepLink()} target="_blank" rel="noreferrer" className="hidden hover:text-white sm:inline">
          Бот
        </a>
        <HeaderAuth />
      </nav>
    </header>
  );
}
