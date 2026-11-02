import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "Ygolek",
  description: "Подписка, ключ доступа и инструкция по подключению.",
  robots: { index: false },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

// Мини-апп внутри Telegram-бота: без шапки и видео-фона сайта,
// цвета берутся из темы Telegram (переменные --tg-theme-*).
export default function MiniAppLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      {/* SDK должен выполниться до гидрации React: Telegram передаёт данные
          входа в #хэше адреса, а роутер Next.js успевает его затереть.
          Поэтому обычный синхронный <script>, а не next/script. */}
      {/* eslint-disable-next-line @next/next/no-sync-scripts */}
      <script src="https://telegram.org/js/telegram-web-app.js" />
      {children}
    </>
  );
}
