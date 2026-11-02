import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin", "cyrillic"], variable: "--font-sans", display: "swap" });

export const metadata: Metadata = {
  title: "Ygolek VPN",
  description: "Быстрый и стабильный VPN. Безлимитный трафик, до 5 устройств, оплата в Telegram Stars.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className={inter.variable}>
      <body className="min-h-screen font-sans antialiased">
        <div className="site-bg" aria-hidden="true">
          <video src="/bg.mp4" poster="/bg.jpg" autoPlay muted loop playsInline preload="auto" />
        </div>
        {children}
      </body>
    </html>
  );
}
