import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ygolek VPN",
  description: "Быстрый VPN на VLESS. Дешевле, честнее, без лишнего.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body className="min-h-screen bg-ink font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
