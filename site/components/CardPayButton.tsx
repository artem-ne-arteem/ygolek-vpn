"use client";

import { useState } from "react";
import { Icon } from "@/components/Icon";
import { CARD_PAYMENT_STUB, PLANS } from "@/lib/plans";

/** Кнопка оплаты картой / СБП. Пока платёжка не подключена — заглушка:
 *  по нажатию показывает, что оплата временно недоступна. */
export function CardPayButton({ className = "btn-primary", full = false }: { className?: string; full?: boolean }) {
  const plan = PLANS[0];
  const [shown, setShown] = useState(false);

  return (
    <div className={full ? "w-full" : undefined}>
      <button type="button" onClick={() => setShown(true)} className={`${className}${full ? " w-full" : ""}`}>
        <Icon name="cart" className="h-4 w-4" />
        Оплатить {plan.priceRub} ₽
      </button>
      {shown && (
        <p role="status" className="mt-2 max-w-xs rounded-xl border border-line bg-panel2/70 px-3 py-2 text-xs text-muted">
          {CARD_PAYMENT_STUB}
        </p>
      )}
    </div>
  );
}
