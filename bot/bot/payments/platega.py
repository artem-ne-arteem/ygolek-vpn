"""Клиент к API Platega (оплата картой / СБП) — https://docs.platega.io/

Ссылку на оплату создаёт POST /v2/transaction/process: способ оплаты (карта,
СБП и т.д.) покупатель выбирает сам на странице Platega. Об оплате Platega
сообщает колбэком на сайт (site/app/api/platega/callback), а бот дополнительно
сверяет статус через GET /transaction/{id} — на случай, если колбэк потерялся.
"""

from dataclasses import dataclass

import httpx

from bot.config import Config

API_URL = "https://app.platega.io"


class PlategaError(RuntimeError):
    pass


@dataclass(frozen=True)
class PlategaPayment:
    transaction_id: str
    url: str


class PlategaClient:
    def __init__(self, config: Config):
        self.enabled = bool(config.platega_merchant_id and config.platega_secret)
        self._http = httpx.AsyncClient(
            base_url=API_URL,
            headers={"X-MerchantId": config.platega_merchant_id, "X-Secret": config.platega_secret},
            timeout=20,
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def create_payment(
        self,
        *,
        amount_rub: int,
        description: str,
        order_id: int,
        tg_id: int,
        username: str | None,
        return_url: str,
    ) -> PlategaPayment:
        metadata = {
            # Platega требует стабильный email покупателя; для Telegram —
            # формат {telegram_id}@telegram.org из их документации
            "user_email": f"{tg_id}@telegram.org",
            "userId": str(tg_id),
        }
        if username:
            metadata["userName"] = f"@{username}"

        data = await self._request(
            "POST",
            "/v2/transaction/process",
            json={
                "paymentDetails": {"amount": amount_rub, "currency": "RUB"},
                "description": description,
                "return": return_url,
                "failedUrl": return_url,
                "payload": f"order:{order_id}",
                "orderId": str(order_id),
                "metadata": metadata,
            },
        )
        transaction_id = data.get("transactionId")
        url = data.get("url") or data.get("redirect")
        if not transaction_id or not url:
            raise PlategaError(f"Platega не вернула ссылку на оплату: {data}")
        return PlategaPayment(transaction_id=transaction_id, url=url)

    async def get_status(self, transaction_id: str) -> dict:
        """Транзакция целиком: status (PENDING/CONFIRMED/CANCELED/CHARGEBACKED), paymentDetails…"""
        return await self._request("GET", f"/transaction/{transaction_id}")

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        try:
            resp = await self._http.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise PlategaError(f"Platega недоступна: {exc}") from exc
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.is_error:
            raise PlategaError(
                f"{method} {url} -> {resp.status_code}: {data.get('message') or resp.text[:300]} "
                f"(traceId={data.get('traceId')})"
            )
        return data
