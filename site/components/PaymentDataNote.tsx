import { PRIVACY_URL } from "@/lib/links";

// Что уходит платёжной системе при оплате картой / СБП — показываем рядом с
// кнопками оплаты (требование Platega). Совпадает с metadata в lib/platega.ts.
export const PAYMENT_DATA_TEXT =
  "При оплате картой или СБП платёжной системе Platega передаются ваш Telegram ID " +
  "(как идентификатор вида 123456789@telegram.org), username в Telegram, сумма и описание заказа. " +
  "Данные карты вы вводите на странице Platega — нам они не передаются и у нас не хранятся.";

export function PaymentDataNote({ className = "" }: { className?: string }) {
  return (
    <p className={`text-xs leading-relaxed text-muted ${className}`}>
      {PAYMENT_DATA_TEXT}{" "}
      <a href={PRIVACY_URL} target="_blank" rel="noreferrer" className="underline hover:text-white">
        Политика конфиденциальности
      </a>
    </p>
  );
}
