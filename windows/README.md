# Ygolek VPN для Windows

WPF-приложение (.NET 10). Вход — через Telegram-бота (API сайта `/api/app/*`),
подключение — ядро [sing-box](https://github.com/SagerNet/sing-box) в режиме TUN:
через виртуальный адаптер идёт трафик всех программ. Для адаптера нужны права
администратора, поэтому приложение запрашивает их при запуске.

```
YgolekVpn/      — приложение
  Services/     — API сайта, подписка (ссылки vless://), конфиг и запуск sing-box
ConfigCheck/    — печатает конфиг sing-box для ссылки; CI проверяет его `sing-box check`
scripts/        — fetch-sing-box.ps1 скачивает ядро в YgolekVpn/core/
```

## Сборка

Без Windows-машины — в GitHub Actions (`.github/workflows/windows-client.yml`):
каждый пуш в `windows/` собирает `YgolekVPN-windows-x64.zip` (вкладка Actions →
запуск → Artifacts). Релиз со ссылкой для пользователей:

```bash
git tag windows-v0.1.0
git push origin windows-v0.1.0
```

Локально (нужен .NET 10 SDK):

```powershell
./windows/scripts/fetch-sing-box.ps1
dotnet run --project windows/YgolekVpn
```

Данные приложения — `%AppData%\YgolekVPN`: токен входа (зашифрован DPAPI),
id устройства, конфиг и лог ядра `sing-box.log`.

Приложение не подписано сертификатом, поэтому при первом запуске Windows
SmartScreen покажет предупреждение: «Подробнее» → «Выполнить в любом случае».
