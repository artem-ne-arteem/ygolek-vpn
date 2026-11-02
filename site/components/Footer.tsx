export function Footer() {
  return (
    <footer className="mt-24 border-t border-white/10 px-6 py-8 text-sm text-white/50 md:px-12">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <span>© {new Date().getFullYear()} Ygolek VPN</span>
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <a
            href="https://telegra.ph/Politika-konfidencialnosti-Ygolek-VPN-08-07"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white"
          >
            Политика конфиденциальности
          </a>
          <a
            href="https://telegra.ph/Polzovatelskoe-soglashenie-Ygolek-VPN-08-07"
            target="_blank"
            rel="noreferrer"
            className="hover:text-white"
          >
            Пользовательское соглашение
          </a>
        </div>
        <a href="https://t.me/fyave" target="_blank" rel="noreferrer" className="hover:text-white">
          Поддержка: @fyave
        </a>
      </div>
    </footer>
  );
}
