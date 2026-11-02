// Чисто декоративные "угольки", летящие вверх в hero. Фиксированный набор
// параметров (не Math.random на рендере) — чтобы не ловить hydration
// mismatch между сервером и клиентом.
const PARTICLES = [
  { left: "8%", size: 4, duration: 7, delay: 0 },
  { left: "18%", size: 3, duration: 9, delay: 1.2 },
  { left: "27%", size: 5, duration: 6.5, delay: 2.5 },
  { left: "38%", size: 3, duration: 8, delay: 0.6 },
  { left: "49%", size: 4, duration: 7.5, delay: 3.1 },
  { left: "58%", size: 3, duration: 9.5, delay: 1.8 },
  { left: "68%", size: 5, duration: 6.8, delay: 0.2 },
  { left: "77%", size: 3, duration: 8.4, delay: 2.2 },
  { left: "86%", size: 4, duration: 7.2, delay: 4 },
  { left: "94%", size: 3, duration: 9.1, delay: 1.4 },
];

export function EmberParticles() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      {PARTICLES.map((p, i) => (
        <span
          key={i}
          className="ember-particle"
          style={{
            left: p.left,
            width: p.size,
            height: p.size,
            animationDuration: `${p.duration}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
