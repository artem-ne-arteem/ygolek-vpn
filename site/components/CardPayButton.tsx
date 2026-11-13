"use client";

import { useState } from "react";
import { Icon } from "@/components/Icon";
import { CARD_PAYMENT_STUB, PLANS } from "@/lib/plans";

/** Оплата картой / СБП через Platega. Не вошёл — ведём в личный кабинет;
 *  ключи Platega не заданы — показываем заглушку. */
export function CardPayButton({ className = "btn-primary", full = false }: { className?: string; full?: boolean }) {
  const plan = PLANS[0];
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const pay = async () => {
    setBusy(true);
    setNotice(null);
    try {
      const resp = await fetch("/api/card/checkout", { method: "POST" });
      if (resp.status === 401) {
        window.location.href = "/account";
        return;
      }
      if (resp.status === 503) {
        setNotice(CARD_PAYMENT_STUB);
        return;
      }
      const data = await resp.json();
      if (!resp.ok || !data.url) throw new Error();
      window.location.href = data.url;
    } catch {
      setNotice("Не получилось создать платёж. Попробуй ещё раз через минуту.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className={full ? "w-full" : undefined}>
      <button type="button" onClick={pay} disabled={busy} className={`${className}${full ? " w-full" : ""}`}>
        <Icon name="cart" className="h-4 w-4" />
        {busy ? "Переходим к оплате…" : `Оплатить ${plan.priceRub} ₽`}
      </button>
      {notice && (
        <p role="status" className="mt-2 max-w-xs rounded-xl border border-line bg-panel2/70 px-3 py-2 text-xs text-muted">
          {notice}
        </p>
      )}
    </div>
  );
}
