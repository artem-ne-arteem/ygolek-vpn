import Image from "next/image";
import Link from "next/link";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Reveal } from "@/components/Reveal";
import { botDeepLink } from "@/lib/plans";

const STEPS = [
  {
    title: "1. Установи приложение",
    text: "iOS / Android / macOS / Windows — Happ. Либо v2rayNG (Android) / v2RayTun (iOS), если уже привык к ним.",
  },
  {
    title: "2. Получи ключ",
    text: "В личном кабинете на сайте или в боте — сразу после оплаты подписки.",
  },
  {
    title: "3. Добавь ключ в приложение",
    text: "В приложении выбери «Добавить по ссылке» / «Import from clipboard» и вставь скопированный ключ.",
  },
  {
    title: "4. Подключись",
    text: "Нажми «Подключиться» — готово.",
  },
];

export default function FaqPage() {
  return (
    <>
      <Header />
      <main className="mx-auto max-w-7xl px-6 py-16 md:px-12">
        <h1 className="text-3xl font-bold">Как подключиться</h1>

        <div className="mt-10 grid gap-12 md:grid-cols-[0.85fr_1.8fr] md:items-center">
          <Reveal>
            <div className="flex flex-col gap-8">
              {STEPS.map((step) => (
                <div key={step.title}>
                  <h2 className="font-semibold text-accent">{step.title}</h2>
                  <p className="mt-2 text-white/70">{step.text}</p>
                </div>
              ))}
            </div>
          </Reveal>

          <Reveal delay={150}>
            <div className="relative mx-auto w-full max-w-md md:ml-auto md:mr-0 md:max-w-4xl">
              <div className="ember-glow ember-glow-1 left-1/2 top-1/4 h-96 w-96 -translate-x-1/2" />
              <Image
                src="/happ-app-store.png"
                alt="Приложение Happ в App Store"
                width={2000}
                height={1786}
                className="relative w-full drop-shadow-2xl"
                priority={false}
              />
            </div>
          </Reveal>
        </div>

        <div className="mt-12 flex flex-wrap gap-3">
          <Link href="/account" className="shine glow-cta rounded-full bg-accent px-6 py-3 font-semibold text-ink">
            Личный кабинет
          </Link>
          <a
            href={botDeepLink()}
            target="_blank"
            rel="noreferrer"
            className="shine rounded-full border border-white/20 px-6 py-3 font-semibold text-white transition-colors hover:border-white/40"
          >
            Открыть бота
          </a>
        </div>
      </main>
      <Footer />
    </>
  );
}
