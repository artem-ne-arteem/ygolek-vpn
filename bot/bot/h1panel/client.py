"""Клиент к API панели H1 (h1cloud) — https://my.h1cloud.net/api-docs#h1-panel-api

Авторизация — токен панели из раздела «API-доступ» (не ключ кабинета h1_…).
В mock-режиме (H1_PANEL_MOCK=true в .env) отдаёт фейковую ссылку, чтобы
можно было прогнать весь флоу бота без обращения к панели.
"""

import uuid
from urllib.parse import quote

import httpx

from bot.config import Config
from bot.plans import DEVICE_LIMIT


class H1PanelError(RuntimeError):
    pass


class H1PanelClient:
    def __init__(self, config: Config):
        self._config = config
        self._http = httpx.AsyncClient(
            base_url=config.h1_panel_url.rstrip("/"),
            headers={"Authorization": f"Bearer {config.h1_panel_token}"},
            timeout=15,
        )

    async def close(self) -> None:
        await self._http.aclose()

    async def upsert_user(self, *, username: str, days: int, traffic_gb: int | None) -> str:
        """Создаёт клиента или продлевает существующего на `days` дней.

        Возвращает subscription-ссылку, которую вставляют в Happ/v2rayNG.
        """
        if self._config.h1_panel_mock:
            return self._mock_subscription_url(username)

        # 0 в панели = безлимит, у нас безлимит — None
        traffic_limit_gb = traffic_gb or 0

        existing = await self._get_client(username)
        if existing is None:
            payload: dict = {
                "name": username,
                "uuid": str(uuid.uuid4()),
                "days": days,
                "traffic_limit_gb": traffic_limit_gb,
                "device_limit": DEVICE_LIMIT,
            }
            if self._config.h1_panel_inbound_ids:
                payload["inbound_ids"] = self._config.h1_panel_inbound_ids
                payload["manual"] = True
            if self._config.h1_panel_channels:
                payload["channels"] = self._config.h1_panel_channels
            client = await self._request("POST", "/api/create", json=payload)
        else:
            # PATCH с days продлевает от max(текущий срок, сейчас) — так же
            # считает и record_subscription в БД бота
            client = await self._request(
                "PATCH",
                f"/api/clients/{quote(username, safe='')}",
                json={"days": days, "traffic_limit_gb": traffic_limit_gb, "device_limit": DEVICE_LIMIT},
            )

        url = self._extract_sub_url(client)
        if url is None:
            # на случай, если PATCH/POST не вернул ссылку — дочитываем клиента
            fetched = await self._get_client(username)
            url = self._extract_sub_url(fetched) if fetched else None
        if url is None:
            raise H1PanelError(f"Панель не вернула ссылку подписки для {username}: {client}")
        return url

    async def get_subscription_url(self, username: str) -> str | None:
        """Возвращает текущую subscription-ссылку без изменения срока/лимита."""
        if self._config.h1_panel_mock:
            return self._mock_subscription_url(username)

        client = await self._get_client(username)
        if client is None:
            return None
        return self._extract_sub_url(client)

    async def _get_client(self, username: str) -> dict | None:
        try:
            resp = await self._http.get(f"/api/clients/{quote(username, safe='')}")
        except httpx.HTTPError as exc:
            raise H1PanelError(f"Панель недоступна: {exc}") from exc
        if resp.status_code == 404:
            return None
        return self._unwrap(resp)

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        try:
            resp = await self._http.request(method, url, **kwargs)
        except httpx.HTTPError as exc:
            raise H1PanelError(f"Панель недоступна: {exc}") from exc
        return self._unwrap(resp)

    @staticmethod
    def _unwrap(resp: httpx.Response) -> dict:
        try:
            data = resp.json()
        except ValueError:
            data = {}
        if resp.is_error or data.get("ok") is False:
            raise H1PanelError(
                f"{resp.request.method} {resp.request.url.path} -> {resp.status_code}: "
                f"{data.get('error') or resp.text[:300]}"
            )
        return data.get("client", data)

    @staticmethod
    def _extract_sub_url(client: dict) -> str | None:
        return client.get("subscription_url") or client.get("sub_url") or None

    @staticmethod
    def _mock_subscription_url(username: str) -> str:
        return f"https://example.invalid/sub/{username}/mock-h1-config"
