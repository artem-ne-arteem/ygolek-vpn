import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { PlanCard } from "@/components/PlanCard";
import { Reveal } from "@/components/Reveal";
import { EmberParticles } from "@/components/EmberParticles";
import { HeroGlow } from "@/components/HeroGlow";
import { Marquee } from "@/components/Marquee";
import { PLANS, TRIAL } from "@/lib/plans";

const STEPS = [
  {
    n: "01",
    title: "Заходишь",
    text: "Через Telegram — на сайте или в боте, аккаунт общий.",
  },
  {
    n: "02",
    title: "Берёшь ключ",
    text: TRIAL.enabled
      ? `Пробный период ${TRIAL.days} дня бесплатно или сразу тариф.`
      : "Оформляешь подписку и оплачиваешь в Telegram Stars.",
  },
  {
    n: "03",
    title: "Подключаешься",
    text: "Вставляешь ключ в Happ или v2rayNG — готово.",
  },
];

const FEATURES = [
  {
    title: "VLESS + Reality",
    text: "Протокол, который сложно отличить от обычного HTTPS-трафика.",
  },
  {
    title: "Happ и v2rayNG",
    text: "Один ключ — вставляешь в привычное приложение, ничего дополнительно ставить не нужно.",
  },
  {
    title: "Честные тарифы",
    text: "Оплата Telegram Stars, без скрытых комиссий и автосписаний без предупреждения.",
  },
];

export default function Home() {
  return (
    <>
      <Header />

      <main>
        <HeroGlow>
          <section className="relative mx-auto max-w-3xl overflow-hidden px-6 py-20 text-center md:px-12 md:py-32">
            <div className="ember-glow ember-glow-1 left-1/2 top-0 h-72 w-72 -translate-x-1/2" />
            <div className="ember-glow ember-glow-2 bottom-0 right-0 h-64 w-64" />
            <EmberParticles />

            <div className="relative z-10">
              <h1 className="text-5xl font-bold leading-[1.05] tracking-tight md:text-7xl">
                VPN, который просто{" "}
                <span className="bg-gradient-to-r from-accent to-accent2 bg-clip-text text-transparent">
                  работает
                </span>
              </h1>
              <p className="mx-auto mt-6 max-w-xl text-lg text-white/60">
                Без переплат за бренд. Оформление за минуту — на сайте или в
                Telegram-боте, ключ подходит для Happ и v2rayNG.
              </p>
              <div className="mt-10 flex flex-col items-center justify-center gap-3 md:flex-row">
                <Link
                  href="/account"
                  className="shine glow-cta rounded-full bg-accent px-6 py-3 font-semibold text-ink"
                >
                  {TRIAL.enabled ? `Попробовать ${TRIAL.days} дня бесплатно` : "Подключить VPN"}
                </Link>
                <a
                  href="#plans"
                  className="shine rounded-full border border-white/20 px-6 py-3 font-semibold text-white transition-colors hover:border-white/40"
                >
                  Смотреть цену
                </a>
              </div>
              {TRIAL.enabled && (
                <p className="mt-4 text-sm text-white/40">
                  Пробный доступ — {TRIAL.trafficLabel}, без привязки карты
                </p>
              )}
            </div>
          </section>
        </HeroGlow>

        <Marquee />

        <div className="px-6 md:px-12">
          <section className="mx-auto max-w-5xl py-12">
            <Reveal>
              <h2 className="text-center text-sm font-semibold uppercase tracking-widest text-white/40">
                Как это работает
              </h2>
            </Reveal>
            <div className="mt-8 grid gap-6 md:grid-cols-3">
              {STEPS.map((step, i) => (
                <Reveal key={step.n} delay={i * 120}>
                  <div className="h-full rounded-2xl border border-white/10 bg-panel p-6 transition-transform duration-300 hover:-translate-y-1">
                    <span className="text-3xl font-bold text-accent/40">{step.n}</span>
                    <h3 className="mt-3 font-semibold">{step.title}</h3>
                    <p className="mt-1 text-sm text-white/60">{step.text}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </section>

          <section id="plans" className="mx-auto max-w-5xl py-16">
            <Reveal>
              <h2 className="text-center text-2xl font-semibold md:text-3xl">Подписка</h2>
            </Reveal>
            <div className="mx-auto mt-10 grid max-w-sm gap-6">
              {PLANS.map((plan, i) => (
                <Reveal key={plan.id} delay={i * 120}>
                  <PlanCard plan={plan} />
                </Reveal>
              ))}
            </div>
          </section>

          <section className="mx-auto max-w-5xl py-16">
            <div className="grid gap-6 md:grid-cols-3">
              {FEATURES.map((item, i) => (
                <Reveal key={item.title} delay={i * 120}>
                  <div className="h-full rounded-2xl border border-white/10 bg-panel p-6 transition-colors hover:border-accent/30">
                    <h3 className="font-semibold">{item.title}</h3>
                    <p className="mt-2 text-sm text-white/60">{item.text}</p>
                  </div>
                </Reveal>
              ))}
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </>
  );
}
