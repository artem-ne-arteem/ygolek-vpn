"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CardPayButton } from "@/components/CardPayButton";
import { Icon, type IconName } from "@/components/Icon";
import { TelegramLoginButton } from "@/components/TelegramLoginButton";
import { ActionCard, Chip, InfoTable, LinksCard, Logo, StatCard } from "@/components/ui";
import { PRIVACY_URL, SUPPORT_URL, TERMS_URL } from "@/lib/links";
import { DEVICE_LIMIT, PLANS, TRIAL, botDeepLink } from "@/lib/plans";

type Me = {
  tgId: number;
  username: string | null;
  trialUsed: boolean;
  subscription: { planId: string; expiresAt: string } | null;
  key: string | null;
};

const plan = PLANS[0];

function daysLeft(expiresAt: string): number {
  return Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 86_400_000));
}

function daysWord(n: number): string {
  if (n % 10 === 1 && n % 100 !== 11) return "день";
  if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)) return "дня";
  return "дней";
}

export default function AccountPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const load = () => {
    fetch("/api/me")
      .then(async (r) => setMe(r.ok ? await r.json() : null))
      .catch(() => setMe(null))
      .finally(() => setLoading(false));
  };

  useEffect(load, []);

  const activateTrial = async () => {
    setBusy("trial");
    setError(null);
    const resp = await fetch("/api/trial", { method: "POST" });
    if (resp.ok) {
      load();
    } else {
      const data = await resp.json();
      setError(
        data.error === "marzban_unavailable"
          ? "VPN-сервер сейчас недоступен, попробуй позже"
          : "Не получилось активировать пробный период"
      );
    }
    setBusy(null);
  };

  const checkout = async () => {
    setBusy("checkout");
    setError(null);
    const resp = await fetch("/api/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ planId: plan.id }),
    });
    if (resp.ok) {
      const data = await resp.json();
      window.open(data.url, "_blank");
    } else {
      setError("Не получилось создать счёт на оплату. Попробуй ещё раз или оплати в боте.");
    }
    setBusy(null);
  };

  const logout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/");
    router.refresh();
  };

  const copyKey = async () => {
    if (!me?.key) return;
    await navigator.clipboard.writeText(me.key);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const sub = me?.subscription ?? null;
  const left = sub ? daysLeft(sub.expiresAt) : 0;
  const displayName = me ? (me.username ? `@${me.username}` : `id${me.tgId}`) : "";

  return (
    <div className="mx-auto flex min-h-screen max-w-[1400px] flex-col gap-4 p-3 md:p-4 lg:flex-row">
      <Sidebar
        displayName={me ? displayName : null}
        onCheckout={me ? checkout : undefined}
        checkoutLabel={`${sub ? "Продлить" : "Оформить"} за ${plan.priceStars} ⭐`}
        busy={busy === "checkout"}
        onLogout={me ? logout : undefined}
      />

      <main className="flex min-w-0 flex-1 flex-col gap-4 lg:py-2">
        {loading && <div className="card p-6 text-muted">Загрузка…</div>}

        {!loading && !me && (
          <div className="card mx-auto mt-10 w-full max-w-md p-8 text-center">
            <span className="icon-box mx-auto">
              <Icon name="user" />
            </span>
            <h1 className="mt-4 text-xl font-semibold">Вход в личный кабинет</h1>
            <p className="mt-2 text-sm text-muted">
              Войди через Telegram — это тот же аккаунт, что и в боте. Подписка и ключ подтянутся автоматически.
            </p>
            <div className="mt-6 flex justify-center">
              <TelegramLoginButton />
            </div>
          </div>
        )}

        {!loading && me && (
          <>
            {error && (
              <div className="flex items-start gap-3 rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-red-200">
                <Icon name="alert" className="mt-0.5 h-5 w-5 shrink-0 text-danger" />
                {error}
              </div>
            )}

            {/* Подписка + счётчики */}
            <div className="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
              <section className="card p-6">
                <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="label-dot">Подписка</p>
                    {sub ? (
                      <>
                        <p className="mt-3 text-4xl font-bold tracking-tight">
                          {left} <span className="text-xl font-medium text-muted">{daysWord(left)}</span>
                        </p>
                        <p className="mt-1 text-sm text-muted">
                          Активна до {new Date(sub.expiresAt).toLocaleDateString("ru-RU")}
                        </p>
                      </>
                    ) : (
                      <>
                        <p className="mt-3 text-3xl font-bold tracking-tight">Нет подписки</p>
                        <p className="mt-1 text-sm text-muted">Оформи подписку — ключ появится здесь сразу после оплаты.</p>
                      </>
                    )}
                    <div className="mt-5 flex flex-wrap gap-2">
                      <button onClick={checkout} disabled={busy === "checkout"} className="btn-primary">
                        {busy === "checkout" ? "Создаём счёт…" : `${sub ? "Продлить" : "Оформить"} за ${plan.priceStars} ⭐`}
                      </button>
                      <CardPayButton className="btn-ghost" />
                      {TRIAL.enabled && !me.trialUsed && !sub && (
                        <button onClick={activateTrial} disabled={busy === "trial"} className="btn-ghost">
                          {busy === "trial" ? "Активируем…" : `Попробовать ${TRIAL.days} дня`}
                        </button>
                      )}
                      <a href={botDeepLink()} target="_blank" rel="noreferrer" className="btn-ghost">
                        Открыть бота
                      </a>
                    </div>
                  </div>
                  <div className="rounded-xl border border-line bg-panel2/60 p-4 sm:min-w-[180px]">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted">Тариф</p>
                    <p className="mt-2 text-lg font-semibold">{plan.title}</p>
                    <p className="text-sm text-muted">{plan.priceRub} ₽ картой или {plan.priceStars} ⭐ в Telegram</p>
                  </div>
                </div>
              </section>

              <div className="grid gap-4 sm:grid-cols-3 xl:grid-cols-1">
                <StatCard
                  value={sub ? "активна" : "нет"}
                  label="статус подписки"
                  icon={sub ? "check" : "alert"}
                />
                <StatCard value={`до ${DEVICE_LIMIT}`} label="устройств одновременно" icon="devices" />
                <StatCard value="Безлимит" label="трафик без лимита по объёму" icon="infinity" />
              </div>
            </div>

            {/* Быстрые действия */}
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <ActionCard
                icon="cart"
                title={sub ? "Продлить подписку" : "Оформить подписку"}
                text={`${plan.priceRub} ₽ или ${plan.priceStars} ⭐ за ${plan.days} дней, ключ не меняется`}
                onClick={checkout}
              />
              <ActionCard icon="book" title="Как подключить" text="Пошаговая инструкция для всех устройств" href="/faq" />
              <ActionCard icon="send" title="Telegram-бот" text="Ключ, оплата и напоминания о продлении" href={botDeepLink()} />
              <ActionCard icon="chat" title="Поддержка" text="Чат с командой в Telegram" href={SUPPORT_URL} />
            </div>

            {/* Ключ + ссылки */}
            <div className="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
              <section id="key" className="card min-w-0 scroll-mt-4 p-6">
                <p className="label-dot">Подключение</p>
                <h2 className="mt-1 text-lg font-semibold">Ключ доступа</h2>

                <div className="mt-5">
                  <InfoTable
                    rows={[
                      { label: "Аккаунт", value: <Chip>{displayName}</Chip> },
                      { label: "Тариф", value: sub ? plan.title : "—" },
                      {
                        label: "Действует до",
                        value: sub ? new Date(sub.expiresAt).toLocaleDateString("ru-RU") : "—",
                      },
                    ]}
                  />
                </div>

                {sub && me.key ? (
                  <>
                    <div className="mt-4 flex flex-col gap-2 sm:flex-row">
                      <code className="min-w-0 flex-1 overflow-x-auto whitespace-nowrap rounded-xl border border-line bg-ink/60 px-4 py-3 font-mono text-xs text-white/90">
                        {me.key}
                      </code>
                      <button onClick={copyKey} className="btn-ghost shrink-0">
                        <Icon name={copied ? "check" : "copy"} className="h-4 w-4" />
                        {copied ? "Скопировано" : "Копировать"}
                      </button>
                    </div>
                    <div className="mt-4 flex items-start gap-3 rounded-xl border border-danger/30 bg-danger/[0.07] p-4 text-sm">
                      <Icon name="alert" className="mt-0.5 h-5 w-5 shrink-0 text-danger" />
                      <div>
                        <p className="font-medium text-red-300">Ключ личный — не публикуй его</p>
                        <p className="mt-1 text-muted">
                          Одной подпиской можно пользоваться на {DEVICE_LIMIT} устройствах. Если ключ утёк — напиши в
                          поддержку, выпустим новый.
                        </p>
                      </div>
                    </div>
                  </>
                ) : sub ? (
                  <p className="mt-4 text-sm text-muted">
                    Не получилось загрузить ключ с сервера. Обнови страницу или возьми ключ в боте.
                  </p>
                ) : (
                  <p className="mt-4 text-sm text-muted">Ключ появится здесь после оплаты подписки.</p>
                )}
              </section>

              <LinksCard
                links={[
                  { label: "Как подключиться", href: "/faq" },
                  { label: "Telegram-бот", href: botDeepLink() },
                  { label: "Поддержка", href: SUPPORT_URL },
                  { label: "Пользовательское соглашение", href: TERMS_URL },
                  { label: "Политика конфиденциальности", href: PRIVACY_URL },
                ]}
              />
            </div>
          </>
        )}
      </main>
    </div>
  );
}

function Sidebar({
  displayName,
  onCheckout,
  checkoutLabel,
  busy,
  onLogout,
}: {
  displayName: string | null;
  onCheckout?: () => void;
  checkoutLabel: string;
  busy: boolean;
  onLogout?: () => void;
}) {
  const nav: { label: string; href: string; icon: IconName; active?: boolean }[] = [
    { label: "Главная", href: "/account", icon: "home", active: true },
    { label: "Ключ доступа", href: "/account#key", icon: "key" },
    { label: "Как подключить", href: "/faq", icon: "book" },
    { label: "Поддержка", href: SUPPORT_URL, icon: "chat" },
    { label: "Документы", href: TERMS_URL, icon: "doc" },
  ];

  return (
    <aside className="card flex shrink-0 flex-col gap-4 p-4 lg:sticky lg:top-4 lg:h-[calc(100vh-2rem)] lg:w-64">
      <div className="flex items-center justify-between px-1 pt-1">
        <Logo />
        <Link href="/" className="text-xs text-muted hover:text-white lg:hidden">
          На сайт
        </Link>
      </div>

      {onCheckout && (
        <button onClick={onCheckout} disabled={busy} className="btn-primary w-full">
          <Icon name="cart" className="h-4 w-4" />
          {busy ? "Создаём счёт…" : checkoutLabel}
        </button>
      )}
      {onCheckout && <CardPayButton className="btn-ghost" full />}

      <div>
        <p className="hidden px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted lg:block">
          Кабинет
        </p>
        <nav className="-mx-1 mt-2 flex gap-1 overflow-x-auto px-1 pb-1 lg:mx-0 lg:flex-col lg:overflow-visible lg:px-0 lg:pb-0">
          {nav.map((item) => {
            const external = item.href.startsWith("http");
            const className = `flex shrink-0 items-center gap-3 rounded-xl px-3 py-2 text-sm transition-colors ${
              item.active
                ? "bg-accent text-white shadow-glow"
                : "text-white/80 hover:bg-panel2 hover:text-white"
            }`;
            const content = (
              <>
                <Icon name={item.icon} className="h-4 w-4" />
                {item.label}
              </>
            );
            return external ? (
              <a key={item.label} href={item.href} target="_blank" rel="noreferrer" className={className}>
                {content}
              </a>
            ) : (
              <Link key={item.label} href={item.href} className={className}>
                {content}
              </Link>
            );
          })}
        </nav>
      </div>

      {displayName && (
        <div className="mt-auto hidden items-center gap-3 rounded-xl border border-line bg-panel2/60 p-3 lg:flex">
          <span className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/15 text-accent">
            <Icon name="user" className="h-4 w-4" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">{displayName}</p>
            <p className="text-xs text-muted">Telegram</p>
          </div>
          {onLogout && (
            <button onClick={onLogout} title="Выйти" className="text-muted hover:text-white">
              <Icon name="logout" className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
      {onLogout && (
        <button onClick={onLogout} className="text-left text-xs text-muted hover:text-white lg:hidden">
          Выйти из аккаунта
        </button>
      )}
    </aside>
  );
}
