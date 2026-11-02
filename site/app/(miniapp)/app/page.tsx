"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Icon, type IconName } from "@/components/Icon";
import { DEVICE_LIMIT, PLANS } from "@/lib/plans";
import { SUPPORT_URL } from "@/lib/links";

// Минимальные типы Telegram WebApp API, которые здесь используются
type MainButton = {
  setText(text: string): void;
  show(): void;
  hide(): void;
  enable(): void;
  disable(): void;
  showProgress(leaveActive?: boolean): void;
  hideProgress(): void;
  onClick(cb: () => void): void;
  offClick(cb: () => void): void;
};

type TgWebApp = {
  initData: string;
  initDataUnsafe: { user?: { first_name?: string } };
  colorScheme: "light" | "dark";
  ready(): void;
  expand(): void;
  MainButton: MainButton;
  HapticFeedback?: {
    notificationOccurred(type: "success" | "error" | "warning"): void;
    impactOccurred(style: "light" | "medium"): void;
  };
  openInvoice(url: string, cb: (status: "paid" | "cancelled" | "failed" | "pending") => void): void;
  openTelegramLink(url: string): void;
  setHeaderColor?(color: string): void;
  setBackgroundColor?(color: string): void;
};

declare global {
  interface Window {
    Telegram?: { WebApp: TgWebApp };
  }
}

type Me = {
  firstName: string | null;
  username: string | null;
  subscription: { expiresAt: string } | null;
  key: string | null;
  deviceLimit?: number;
};

const plan = PLANS[0];

const GUIDES: { id: string; label: string; app: string; steps: string[] }[] = [
  {
    id: "ios",
    label: "iPhone",
    app: "Happ или v2RayTun из App Store",
    steps: ["Установи приложение", "Скопируй ключ выше", "В приложении нажми «+» → «Вставить из буфера»", "Нажми «Подключиться»"],
  },
  {
    id: "android",
    label: "Android",
    app: "Happ или v2rayNG из Google Play",
    steps: ["Установи приложение", "Скопируй ключ выше", "Нажми «+» → «Импорт из буфера обмена»", "Нажми кнопку подключения"],
  },
  {
    id: "desktop",
    label: "Windows / Mac",
    app: "Happ для компьютера",
    steps: ["Установи Happ", "Скопируй ключ выше", "Добавь его через «+» → «Вставить из буфера»", "Нажми «Подключиться»"],
  },
];

function daysLeft(expiresAt: string) {
  return Math.max(0, Math.floor((new Date(expiresAt).getTime() - Date.now()) / 86_400_000));
}

function daysWord(n: number) {
  if (n % 10 === 1 && n % 100 !== 11) return "день";
  if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 12 || n % 100 > 14)) return "дня";
  return "дней";
}

export default function MiniApp() {
  const [tg, setTg] = useState<TgWebApp | null>(null);
  const [outside, setOutside] = useState(false);
  const [me, setMe] = useState<Me | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [guide, setGuide] = useState(GUIDES[0].id);
  const [justPaid, setJustPaid] = useState(false);
  const buying = useRef(false);

  // ждём SDK Telegram; если за 3 секунды его нет или нет initData — открыто не из бота
  useEffect(() => {
    let tries = 0;
    const timer = setInterval(() => {
      const webApp = window.Telegram?.WebApp;
      if (webApp) {
        clearInterval(timer);
        if (!webApp.initData) {
          setOutside(true);
          return;
        }
        webApp.ready();
        webApp.expand();
        setTg(webApp);
      } else if (++tries > 30) {
        clearInterval(timer);
        setOutside(true);
      }
    }, 100);
    return () => clearInterval(timer);
  }, []);

  const load = useCallback(async (): Promise<Me | null> => {
    if (!tg) return null;
    try {
      const resp = await fetch("/api/tg/me", { headers: { "x-telegram-init-data": tg.initData }, cache: "no-store" });
      if (!resp.ok) throw new Error();
      const data: Me = await resp.json();
      setMe(data);
      setError(null);
      return data;
    } catch {
      setError("Не получилось загрузить данные. Закрой и открой приложение ещё раз.");
      return null;
    }
  }, [tg]);

  useEffect(() => {
    load();
  }, [load]);

  // после оплаты бот выдаёт подписку за пару секунд — опрашиваем, пока срок не обновится
  const waitForPayment = useCallback(
    async (previous: string | null) => {
      for (let i = 0; i < 15; i++) {
        await new Promise((r) => setTimeout(r, 2000));
        const data = await load();
        if (data?.subscription && data.subscription.expiresAt !== previous) {
          tg?.HapticFeedback?.notificationOccurred("success");
          setJustPaid(true);
          return;
        }
      }
    },
    [load, tg]
  );

  const buy = useCallback(async () => {
    if (!tg || buying.current) return;
    buying.current = true;
    tg.MainButton.showProgress();
    try {
      const resp = await fetch("/api/tg/checkout", { method: "POST", headers: { "x-telegram-init-data": tg.initData } });
      if (!resp.ok) throw new Error();
      const { url } = await resp.json();
      const previous = me?.subscription?.expiresAt ?? null;
      tg.openInvoice(url, (status) => {
        if (status === "paid") waitForPayment(previous);
        if (status === "failed") tg.HapticFeedback?.notificationOccurred("error");
      });
    } catch {
      setError("Не получилось создать счёт. Попробуй ещё раз.");
      tg.HapticFeedback?.notificationOccurred("error");
    } finally {
      tg.MainButton.hideProgress();
      buying.current = false;
    }
  }, [tg, me, waitForPayment]);

  // нативная кнопка Telegram внизу экрана
  useEffect(() => {
    if (!tg || !me) return;
    tg.MainButton.setText(`${me.subscription ? "Продлить" : "Оформить"} за ${plan.priceStars} ⭐`);
    tg.MainButton.show();
    tg.MainButton.onClick(buy);
    return () => tg.MainButton.offClick(buy);
  }, [tg, me, buy]);

  const copyKey = async () => {
    if (!me?.key) return;
    try {
      await navigator.clipboard.writeText(me.key);
    } catch {
      // старые клиенты Telegram без доступа к буферу — выделяем текст
      const el = document.getElementById("key-text");
      if (el) window.getSelection()?.selectAllChildren(el);
    }
    tg?.HapticFeedback?.impactOccurred("light");
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const openSupport = () => tg?.openTelegramLink(SUPPORT_URL);

  if (outside) {
    return (
      <Shell>
        <div className="flex min-h-[80vh] flex-col items-center justify-center gap-3 text-center">
          <span className="ma-icon">
            <Icon name="send" />
          </span>
          <p className="text-lg font-semibold">Открой приложение через Telegram</p>
          <p className="ma-hint text-sm">Кнопка «Приложение» есть в меню бота.</p>
        </div>
      </Shell>
    );
  }

  if (!me) {
    return (
      <Shell>
        {error ? (
          <p className="ma-card p-4 text-sm">{error}</p>
        ) : (
          <div className="flex flex-col gap-3">
            {[96, 140, 120].map((h) => (
              <div key={h} className="ma-card animate-pulse" style={{ height: h }} />
            ))}
          </div>
        )}
      </Shell>
    );
  }

  const sub = me.subscription;
  const left = sub ? daysLeft(sub.expiresAt) : 0;
  const progress = sub ? Math.min(100, Math.round((left / plan.days) * 100)) : 0;
  const deviceLimit = me.deviceLimit ?? DEVICE_LIMIT;
  const activeGuide = GUIDES.find((g) => g.id === guide) ?? GUIDES[0];

  return (
    <Shell>
      <header className="flex items-center gap-3 px-1">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/miniapp-logo.jpg" alt="" className="h-10 w-10 rounded-xl bg-white object-cover" />
        <div>
          <p className="text-[17px] font-semibold leading-tight">Ygolek</p>
          <p className="ma-hint text-sm">{me.firstName ? `Привет, ${me.firstName}!` : "Привет!"}</p>
        </div>
      </header>

      {error && <p className="ma-card p-3 text-sm text-red-400">{error}</p>}

      {justPaid && (
        <div className="ma-card flex items-center gap-3 p-4">
          <span className="ma-icon">
            <Icon name="check" />
          </span>
          <p className="text-sm font-medium">Оплата прошла, подписка продлена. Ключ остался прежним.</p>
        </div>
      )}

      {/* Статус */}
      <section className="ma-card p-5">
        <p className="ma-section">Подписка</p>
        {sub ? (
          <>
            <div className="mt-2 flex items-end justify-between">
              <p className="text-4xl font-bold tracking-tight">
                {left} <span className="ma-hint text-lg font-medium">{daysWord(left)}</span>
              </p>
              <span className="ma-badge">
                активна
              </span>
            </div>
            <div className="ma-progress mt-4">
              <div className="ma-progress-bar" style={{ width: `${progress}%` }} />
            </div>
            <p className="ma-hint mt-2 text-sm">до {new Date(sub.expiresAt).toLocaleDateString("ru-RU")}</p>
          </>
        ) : (
          <>
            <p className="mt-2 text-2xl font-bold">Нет подписки</p>
            <p className="ma-hint mt-1 text-sm">Оформи подписку кнопкой внизу — ключ появится здесь сразу после оплаты.</p>
          </>
        )}
      </section>

      {/* Ключ */}
      {sub && (
        <section className="ma-card p-5">
          <p className="ma-section">Ключ доступа</p>
          {me.key ? (
            <>
              <p id="key-text" className="ma-key mt-3 break-all font-mono text-xs leading-relaxed">
                {me.key}
              </p>
              <button onClick={copyKey} className="ma-button mt-3 w-full">
                <Icon name={copied ? "check" : "copy"} className="h-4 w-4" />
                {copied ? "Скопировано" : "Скопировать ключ"}
              </button>
              <p className="ma-hint mt-3 text-xs">Ключ личный — не пересылай его. Работает на {deviceLimit} устройствах.</p>
            </>
          ) : (
            <p className="ma-hint mt-2 text-sm">Не получилось загрузить ключ. Возьми его в боте кнопкой «Мой ключ».</p>
          )}
        </section>
      )}

      {/* Инструкция */}
      <section className="ma-card p-5">
        <p className="ma-section">Как подключить</p>
        <div className="ma-tabs mt-3">
          {GUIDES.map((g) => (
            <button
              key={g.id}
              onClick={() => {
                setGuide(g.id);
                tg?.HapticFeedback?.impactOccurred("light");
              }}
              className={g.id === guide ? "ma-tab ma-tab-active" : "ma-tab"}
            >
              {g.label}
            </button>
          ))}
        </div>
        <p className="ma-hint mt-3 text-sm">Приложение: {activeGuide.app}</p>
        <ol className="mt-3 flex flex-col gap-2">
          {activeGuide.steps.map((step, i) => (
            <li key={step} className="flex items-center gap-3 text-sm">
              <span className="ma-step-num">
                {i + 1}
              </span>
              {step}
            </li>
          ))}
        </ol>
      </section>

      {/* Тариф и поддержка */}
      <section className="ma-card ma-divide">
        <Row icon="star" title={`${plan.title} — ${plan.priceStars} ⭐`} text={`Безлимит трафика · до ${deviceLimit} устройств`} />
        <Row icon="chat" title="Поддержка" text="@ygolek_support" onClick={openSupport} />
      </section>
    </Shell>
  );
}

function Row({ icon, title, text, onClick }: { icon: IconName; title: string; text: string; onClick?: () => void }) {
  const inner = (
    <>
      <span className="ma-icon">
        <Icon name={icon} className="h-5 w-5" />
      </span>
      <div className="min-w-0 flex-1 text-left">
        <p className="text-[15px] font-medium">{title}</p>
        <p className="ma-hint text-sm">{text}</p>
      </div>
      {onClick && <Icon name="arrow" className="ma-hint h-4 w-4" />}
    </>
  );
  return onClick ? (
    <button onClick={onClick} className="flex w-full items-center gap-3 p-4 active:opacity-70">
      {inner}
    </button>
  ) : (
    <div className="flex items-center gap-3 p-4">{inner}</div>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="miniapp">
      <main className="mx-auto flex min-h-screen max-w-md flex-col gap-3 px-3 pb-6 pt-4">{children}</main>
    </div>
  );
}
