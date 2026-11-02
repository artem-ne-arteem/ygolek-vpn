const ITEMS = [
  "VLESS + Reality",
  "Без логов трафика",
  "Happ",
  "v2rayNG",
  "v2RayTun",
  "Telegram Stars",
  "Ключ за секунды",
];

export function Marquee() {
  const items = [...ITEMS, ...ITEMS];
  return (
    <div className="overflow-hidden border-y border-white/10 bg-panel/50 py-4">
      <div className="marquee-track gap-10">
        {items.map((item, i) => (
          <span key={i} className="shrink-0 whitespace-nowrap text-sm text-white/40">
            <span className="text-accent">✦</span> {item}
          </span>
        ))}
      </div>
    </div>
  );
}
