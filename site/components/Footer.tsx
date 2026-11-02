import { PRIVACY_URL, SUPPORT_URL, TERMS_URL } from "@/lib/links";

export function Footer() {
  return (
    <footer className="mt-16 border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-8 text-sm text-muted md:flex-row md:items-center md:justify-between md:px-6">
        <span>© {new Date().getFullYear()} Ygolek VPN</span>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <a href={PRIVACY_URL} target="_blank" rel="noreferrer" className="hover:text-white">
            Политика конфиденциальности
          </a>
          <a href={TERMS_URL} target="_blank" rel="noreferrer" className="hover:text-white">
            Пользовательское соглашение
          </a>
          <a href={SUPPORT_URL} target="_blank" rel="noreferrer" className="hover:text-white">
            Поддержка: @ygolek_support
          </a>
        </div>
      </div>
    </footer>
  );
}
