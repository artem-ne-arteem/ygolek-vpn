"""Клиент к REST API Marzban (панель управления Xray/VLESS-нодой).

Пока реальная нода не поднята — работает в mock-режиме (MARZBAN_MOCK=true в
.env) и отдаёт фейковую, но валидную по формату vless-подписку, чтобы можно
было прогнать весь флоу бота без сервера. Как только infra/setup-marzban.sh
отработает на реальном VPS — переключи MARZBAN_MOCK=false и заполни
MARZBAN_API_URL/MARZBAN_ADMIN_USERNAME/MARZBAN_ADMIN_PASSWORD.
"""

import datetime as dt

import httpx

from bot.config import Config


class MarzbanError(RuntimeError):
    pass


class MarzbanClient:
    def __init__(self, config: Config):
        self._config = config
        self._token: str | None = None
        self._http = httpx.AsyncClient(base_url=config.marzban_api_url, timeout=15)

    async def close(self) -> None:
        await self._http.aclose()

    async def upsert_user(
        self,
        *,
        marzban_username: str,
        days: int,
        traffic_gb: int | None,
    ) -> str:
        """Создаёт пользователя или продлевает существующего.

        Возвращает subscription-ссылку, которую вставляют в Happ/v2rayNG.
        """
        if self._config.marzban_mock:
            return self._mock_subscription_url(marzban_username)

        expire_ts = int((dt.datetime.utcnow() + dt.timedelta(days=days)).timestamp())
        data_limit = None if traffic_gb is None else traffic_gb * 1024 * 1024 * 1024

        await self._ensure_token()

        existing = await self._get_user(marzban_username)
        payload = {
            "username": marzban_username,
            "expire": expire_ts,
            "data_limit": data_limit,
            "status": "active",
        }

        if existing is None:
            payload["proxies"] = {"vless": {"flow": "xtls-rprx-vision"}}
            payload["inbounds"] = {"vless": ["VLESS TCP REALITY"]}
            resp = await self._request("POST", "/api/user", json=payload)
        else:
            resp = await self._request("PUT", f"/api/user/{marzban_username}", json=payload)

        subscription_url = resp.get("subscription_url")
        if not subscription_url:
            raise MarzbanError(f"Marzban не вернул subscription_url: {resp}")

        base = self._config.marzban_sub_domain.rstrip("/")
        if subscription_url.startswith("/"):
            return f"https://{base}{subscription_url}"
        return subscription_url

    async def get_subscription_url(self, marzban_username: str) -> str | None:
        """Возвращает текущую subscription-ссылку без изменения срока/лимита."""
        if self._config.marzban_mock:
            return self._mock_subscription_url(marzban_username)

        await self._ensure_token()
        existing = await self._get_user(marzban_username)
        if existing is None:
            return None

        subscription_url = existing.get("subscription_url")
        if not subscription_url:
            return None

        base = self._config.marzban_sub_domain.rstrip("/")
        if subscription_url.startswith("/"):
            return f"https://{base}{subscription_url}"
        return subscription_url

    async def _get_user(self, marzban_username: str) -> dict | None:
        resp = await self._http.get(
            f"/api/user/{marzban_username}",
            headers=self._auth_header(),
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()

    async def _ensure_token(self) -> None:
        if self._token is not None:
            return
        resp = await self._http.post(
            "/api/admin/token",
            data={
                "username": self._config.marzban_admin_username,
                "password": self._config.marzban_admin_password,
            },
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]

    def _auth_header(self) -> dict:
        return {"Authorization": f"Bearer {self._token}"}

    async def _request(self, method: str, url: str, **kwargs) -> dict:
        resp = await self._http.request(method, url, headers=self._auth_header(), **kwargs)
        if resp.status_code == 401:
            # токен протух — переавторизуемся один раз и повторим запрос
            self._token = None
            await self._ensure_token()
            resp = await self._http.request(method, url, headers=self._auth_header(), **kwargs)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _mock_subscription_url(marzban_username: str) -> str:
        return f"https://sub.ygolek-vpn.online/sub/{marzban_username}/mock-vless-config"
