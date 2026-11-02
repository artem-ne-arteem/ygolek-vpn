import type { Metadata, Viewport } from "next";
import Script from "next/script";

export const metadata: Metadata = {
  title: "Ygolek",
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
      {/* beforeInteractive разрешён только в корневом layout, поэтому грузим
          обычным способом, а страница ждёт появления window.Telegram */}
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" />
      {children}
    </>
  );
}
