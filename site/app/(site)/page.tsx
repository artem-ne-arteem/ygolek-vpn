import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Icon } from "@/components/Icon";
import { Reveal } from "@/components/Reveal";
import { ActionCard, InfoTable, LinksCard, StatCard } from "@/components/ui";
import { PRIVACY_URL, SUPPORT_URL, TERMS_URL } from "@/lib/links";
import { DEVICE_LIMIT, PLANS, botDeepLink } from "@/lib/plans";

const plan = PLANS[0];

const STEPS = [
  { n: "01", title: "Войди через Telegram", text: "На сайте или в боте — аккаунт общий." },
  { n: "02", title: "Оплати подписку", text: `${plan.priceStars} ⭐ в месяц, оплата прямо в Telegram.` },
  { n: "03", title: "Вставь ключ", text: "В Happ или v2rayNG — и нажми «Подключиться»." },
];

export default function Home() {
  return (
    <>
      <Header />

      <main className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 md:px-6 md:py-10">
        {/* Hero + счётчики */}
        <div className="grid gap-4 lg:grid-cols-[1.7fr_1fr]">
          <Reveal>
            <section className="card relative h-full overflow-hidden p-6 md:p-8">
              <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent/20 blur-3xl" />
              <p className="label-dot">VLESS</p>
              <h1 className="mt-4 max-w-xl text-4xl font-bold leading-[1.05] tracking-tight md:text-5xl">
                Быстрый VPN <span className="text-accent2">без лишних настроек</span>
              </h1>
              <p className="mt-4 max-w-lg text-muted">
                Безлимитный трафик и до {DEVICE_LIMIT} устройств на одну подписку. Оформление за минуту —
                на сайте или в Telegram-боте.
              </p>

              <div className="mt-8 flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted">Подписка</p>
                  <p className="mt-1 text-4xl font-bold tracking-tight">
                    {plan.priceStars} ⭐ <span className="text-lg font-medium text-muted">/ месяц</span>
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Link href="/account" className="btn-primary">
                      Подключить VPN
                    </Link>
                    <a href={botDeepLink()} target="_blank" rel="noreferrer" className="btn-ghost">
                      <Icon name="send" className="h-4 w-4" />
                      Открыть бота
                    </a>
                  </div>
                </div>
                <div className="flex flex-col gap-2 text-sm sm:items-end">
                  {["Без логов трафика", "Ключ за минуту", "Поддержка в Telegram"].map((item) => (
                    <span
                      key={item}
                      className="flex w-fit items-center gap-2 whitespace-nowrap rounded-xl border border-line bg-panel2/70 px-3 py-2"
                    >
                      <Icon name="check" className="h-4 w-4 text-accent" />
                      {item}
                    </span>
                  ))}
                </div>
              </div>
            </section>
          </Reveal>

          <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            <Reveal delay={80}>
              <StatCard value={String(DEVICE_LIMIT)} label="устройств на подписку" icon="devices" />
            </Reveal>
            <Reveal delay={160}>
              <StatCard value="Безлимит" label="трафик без лимита по объёму" icon="infinity" />
            </Reveal>
            <Reveal delay={240}>
              <StatCard value="Stars" label="оплата прямо в Telegram" icon="shield" />
            </Reveal>
          </div>
        </div>

        {/* Быстрые действия */}
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ActionCard icon="cart" title="Оформить подписку" text="Оплата в Telegram Stars без лишних шагов" href="/account" />
          <ActionCard icon="user" title="Личный кабинет" text="Ключ, срок подписки и продление" href="/account" />
          <ActionCard icon="book" title="Как подключить" text="Инструкция для iPhone, Android, Windows и Mac" href="/faq" />
          <ActionCard icon="chat" title="Поддержка" text="Ответим в Telegram — @ygolek_support" href={SUPPORT_URL} />
        </div>

        {/* Тариф + ссылки */}
        <div id="plan" className="grid scroll-mt-24 gap-4 lg:grid-cols-[1.7fr_1fr]">
          <Reveal>
            <section className="card h-full p-6">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="label-dot">Тариф</p>
                  <h2 className="mt-1 text-lg font-semibold">Подписка на {plan.title.toLowerCase()}</h2>
                </div>
                <Link href="/account" className="btn-primary">
                  Оформить за {plan.priceStars} ⭐
                </Link>
              </div>
              <div className="mt-5">
                <InfoTable
                  rows={[
                    { label: "Срок", value: `${plan.days} дней` },
                    { label: "Трафик", value: "Безлимит" },
                    { label: "Устройства", value: `до ${DEVICE_LIMIT} одновременно` },
                    { label: "Протокол", value: "VLESS" },
                    { label: "Приложения", value: "Happ, v2rayNG, v2RayTun" },
                    { label: "Оплата", value: "Telegram Stars" },
                  ]}
                />
              </div>
              <p className="mt-4 text-sm text-muted">
                Продление добавляет дни к текущему сроку, ключ остаётся прежним — перенастраивать ничего не нужно.
              </p>
            </section>
          </Reveal>

          <Reveal delay={100}>
            <LinksCard
              links={[
                { label: "Telegram-бот", href: botDeepLink() },
                { label: "Как подключиться", href: "/faq" },
                { label: "Поддержка", href: SUPPORT_URL },
                { label: "Пользовательское соглашение", href: TERMS_URL },
                { label: "Политика конфиденциальности", href: PRIVACY_URL },
              ]}
            />
          </Reveal>
        </div>

        {/* Как это работает */}
        <div className="grid gap-4 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <Reveal key={step.n} delay={i * 100}>
              <div className="card h-full p-5">
                <span className="font-mono text-sm font-semibold text-accent">{step.n}</span>
                <h3 className="mt-3 font-semibold">{step.title}</h3>
                <p className="mt-1 text-sm text-muted">{step.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </main>

      <Footer />
    </>
  );
}
