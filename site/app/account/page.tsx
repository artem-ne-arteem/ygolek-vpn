"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { PLANS, TRIAL } from "@/lib/plans";

type Me = {
  tgId: number;
  username: string | null;
  trialUsed: boolean;
  subscription: { planId: string; expiresAt: string } | null;
  key: string | null;
};

export default function AccountPage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const load = () => {
    fetch("/api/me")
      .then(async (r) => {
        if (!r.ok) {
          router.push("/");
          return;
        }
        setMe(await r.json());
      })
      .finally(() => setLoading(false));
  };

  useEffect(load, [router]);

  const activateTrial = async () => {
    setBusy("trial");
    setError(null);
    const resp = await fetch("/api/trial", { method: "POST" });
    if (resp.ok) {
      load();
    } else {
      const data = await resp.json();
      setError(data.error === "marzban_unavailable" ? "VPN-сервер сейчас недоступен, попробуй позже" : "Не получилось активировать пробный период");
    }
    setBusy(null);
  };

  const checkout = async (planId: string) => {
    setBusy(planId);
    setError(null);
    const resp = await fetch("/api/checkout", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ planId }),
    });
    if (resp.ok) {
      const data = await resp.json();
      window.open(data.url, "_blank");
    } else {
      setError("Не получилось создать счёт на оплату");
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

  return (
    <>
      <Header />
      <main className="mx-auto max-w-2xl px-6 py-16 md:px-12">
        <h1 className="text-3xl font-bold">Личный кабинет</h1>

        {loading && <p className="mt-8 text-white/50">Загрузка…</p>}

        {!loading && me && (
          <div className="mt-8 flex flex-col gap-6">
            {error && (
              <div className="rounded-xl border border-accent/40 bg-accent/10 px-4 py-3 text-sm text-accent">
                {error}
              </div>
            )}

            <div className="rounded-2xl border border-white/10 bg-panel p-6">
              <p className="text-sm text-white/50">Telegram</p>
              <p className="mt-1 font-medium">
                {me.username ? `@${me.username}` : `id${me.tgId}`}
              </p>
            </div>

            {me.subscription ? (
              <div className="rounded-2xl border border-accent/40 bg-accent/5 p-6">
                <p className="text-sm text-white/50">Подписка активна до</p>
                <p className="mt-1 text-xl font-semibold text-accent">
                  {new Date(me.subscription.expiresAt).toLocaleDateString("ru-RU")}
                </p>

                {me.key && (
                  <div className="mt-4">
                    <p className="text-sm text-white/50">Ключ</p>
                    <div className="mt-1 flex items-center gap-2">
                      <code className="flex-1 overflow-x-auto rounded-lg bg-black/30 px-3 py-2 text-xs">
                        {me.key}
                      </code>
                      <button
                        onClick={copyKey}
                        className="shrink-0 rounded-lg border border-white/15 px-3 py-2 text-xs font-medium hover:border-accent/60"
                      >
                        {copied ? "Скопировано" : "Копировать"}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-2xl border border-white/10 bg-panel p-6">
                <p className="text-white/70">Активной подписки нет.</p>
                {TRIAL.enabled && !me.trialUsed && (
                  <button
                    onClick={activateTrial}
                    disabled={busy === "trial"}
                    className="mt-4 rounded-full bg-accent px-5 py-2.5 font-semibold text-ink hover:opacity-90 disabled:opacity-50"
                  >
                    {busy === "trial" ? "Активируем…" : `Попробовать ${TRIAL.days} дня бесплатно`}
                  </button>
                )}
              </div>
            )}

            <div className="rounded-2xl border border-white/10 bg-panel p-6">
              <p className="mb-4 font-semibold">
                {me.subscription ? "Продлить подписку" : "Оформить подписку"}
              </p>
              <div className="flex flex-col gap-3">
                {PLANS.map((plan) => (
                  <button
                    key={plan.id}
                    onClick={() => checkout(plan.id)}
                    disabled={busy === plan.id}
                    className="flex items-center justify-between rounded-xl border border-white/10 px-4 py-3 text-left hover:border-accent/60 disabled:opacity-50"
                  >
                    <span>
                      {plan.title} · {plan.trafficLabel}
                    </span>
                    <span className="font-semibold text-accent">
                      {busy === plan.id ? "…" : `${plan.priceStars} ⭐`}
                    </span>
                  </button>
                ))}
              </div>
            </div>

            <button onClick={logout} className="self-start text-sm text-white/40 hover:text-white/70">
              Выйти
            </button>
          </div>
        )}
      </main>
      <Footer />
    </>
  );
}
