// Оформление сайта: видео-фон есть только на страницах сайта, мини-апп
// в Telegram (app/(miniapp)) живёт без него.
export default function SiteLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <div className="site-bg" aria-hidden="true">
        <video src="/bg.mp4" poster="/bg.jpg" autoPlay muted loop playsInline preload="auto" />
      </div>
      {children}
    </>
  );
}
