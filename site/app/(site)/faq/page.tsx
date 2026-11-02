import Image from "next/image";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Icon, type IconName } from "@/components/Icon";
import { Reveal } from "@/components/Reveal";
import { DEVICE_LIMIT, botDeepLink } from "@/lib/plans";
import { SUPPORT_URL } from "@/lib/links";

const STEPS = [
  {
    title: "Установи приложение",
    text: "iOS, Android, macOS, Windows — Happ. Либо v2rayNG (Android) или v2RayTun (iOS), если уже привык к ним.",
  },
  {
    title: "Получи ключ",
    text: "В личном кабинете на сайте или в боте — сразу после оплаты подписки.",
  },
  {
    title: "Добавь ключ в приложение",
    text: "Выбери «Добавить по ссылке» / «Import from clipboard» и вставь скопированный ключ.",
  },
  {
    title: "Подключись",
    text: "Нажми «Подключиться» — готово. Ключ сам обновляется, перенастраивать ничего не нужно.",
  },
];

const APPS: { platform: string; apps: string; icon: IconName }[] = [
  { platform: "iPhone / iPad", apps: "Happ, v2RayTun", icon: "devices" },
  { platform: "Android", apps: "Happ, v2rayNG", icon: "devices" },
  { platform: "Windows / macOS", apps: "Happ", icon: "devices" },
];

const QUESTIONS = [
  {
    q: "Сколько устройств можно подключить?",
    a: `До ${DEVICE_LIMIT} устройств на одну подписку — телефон, ноутбук, планшет и т.д.`,
  },
  { q: "Есть ли лимит трафика?", a: "Нет, трафик безлимитный." },
  {
    q: "Что будет, когда подписка закончится?",
    a: "Бот напомнит за 3 дня и за сутки. После продления тот же ключ снова заработает.",
  },
  {
    q: "Как оплатить?",
    a: "Telegram Stars — в боте или в личном кабинете на сайте. Звёзды покупаются прямо в Telegram.",
  },
];

export default function FaqPage() {
  return (
    <>
      <Header />
      <main className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-6 md:px-6 md:py-10">
        <div className="grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <Reveal>
            <section className="card h-full p-6 md:p-8">
              <p className="label-dot">Инструкция</p>
              <h1 className="mt-1 text-3xl font-bold tracking-tight">Как подключиться</h1>
              <ol className="mt-6 flex flex-col gap-3">
                {STEPS.map((step, i) => (
                  <li key={step.title} className="flex gap-4 rounded-xl border border-line bg-panel2/50 p-4">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent/15 font-mono text-sm font-semibold text-accent">
                      {i + 1}
                    </span>
                    <div>
                      <h2 className="font-semibold">{step.title}</h2>
                      <p className="mt-1 text-sm text-muted">{step.text}</p>
                    </div>
                  </li>
                ))}
              </ol>
              <div className="mt-6 flex flex-wrap gap-2">
                <Link href="/account" className="btn-primary">
                  Личный кабинет
                </Link>
                <a href={botDeepLink()} target="_blank" rel="noreferrer" className="btn-ghost">
                  <Icon name="send" className="h-4 w-4" />
                  Открыть бота
                </a>
              </div>
            </section>
          </Reveal>

          <Reveal delay={120}>
            <section className="card relative flex h-full items-center justify-center overflow-hidden p-6">
              <div className="pointer-events-none absolute left-1/2 top-1/3 h-72 w-72 -translate-x-1/2 rounded-full bg-accent/20 blur-3xl" />
              <Image
                src="/happ-app-store.png"
                alt="Приложение Happ в App Store"
                width={2000}
                height={1786}
                className="relative w-full max-w-lg drop-shadow-2xl"
              />
            </section>
          </Reveal>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          {APPS.map((item) => (
            <div key={item.platform} className="card flex items-center gap-4 p-5">
              <span className="icon-box">
                <Icon name={item.icon} />
              </span>
              <div>
                <p className="font-semibold">{item.platform}</p>
                <p className="text-sm text-muted">{item.apps}</p>
              </div>
            </div>
          ))}
        </div>

        <section className="card p-6">
          <p className="label-dot">Вопросы</p>
          <h2 className="mt-1 text-lg font-semibold">Частые вопросы</h2>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {QUESTIONS.map((item) => (
              <div key={item.q} className="rounded-xl border border-line bg-panel2/50 p-4">
                <p className="font-medium">{item.q}</p>
                <p className="mt-1 text-sm text-muted">{item.a}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-sm text-muted">
            Не нашёл ответ?{" "}
            <a href={SUPPORT_URL} target="_blank" rel="noreferrer" className="text-accent2 hover:underline">
              Напиши в поддержку
            </a>
            .
          </p>
        </section>
      </main>
      <Footer />
    </>
  );
}
