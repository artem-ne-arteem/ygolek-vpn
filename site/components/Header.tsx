import Link from "next/link";
import { botDeepLink } from "@/lib/plans";
import { HeaderAuth } from "./HeaderAuth";
import { Logo } from "./ui";

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-ink/75 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 md:px-6">
        <Logo />
        <nav className="flex items-center gap-1 text-sm text-muted">
          <Link href="/#plan" className="hidden rounded-lg px-3 py-2 hover:bg-panel2 hover:text-white sm:inline">
            Цена
          </Link>
          <Link href="/faq" className="hidden rounded-lg px-3 py-2 hover:bg-panel2 hover:text-white sm:inline">
            Как подключить
          </Link>
          <a
            href={botDeepLink()}
            target="_blank"
            rel="noreferrer"
            className="hidden rounded-lg px-3 py-2 hover:bg-panel2 hover:text-white md:inline"
          >
            Бот
          </a>
          <div className="ml-2">
            <HeaderAuth />
          </div>
        </nav>
      </div>
    </header>
  );
}
