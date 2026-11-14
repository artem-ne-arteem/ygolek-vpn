# Ygolek VPN для iOS

SwiftUI-приложение и VPN-модуль (Network Extension, Packet Tunnel) с ядром
[sing-box](https://github.com/SagerNet/sing-box). Вход — через Telegram-бота
(API сайта `/api/app/*`), серверы — из подписки панели, как в Windows-клиенте.

```
YgolekVPN/      — приложение: вход, подписка, серверы, кнопка подключения
  Services/     — API сайта, подписка (ссылки vless://), конфиг sing-box, профиль VPN
PacketTunnel/   — VPN-модуль: запускает ядро sing-box внутри NetworkExtension
scripts/        — build-libbox.sh собирает ядро (Libbox.xcframework) для iOS
project.yml     — описание проекта для XcodeGen (сам .xcodeproj не хранится)
```

Части `PacketTunnel/PlatformInterface.swift` и `RunBlocking.swift` основаны на
[sing-box-for-apple](https://github.com/SagerNet/sing-box-for-apple) (GPL-3.0).

## Сборка и установка

Мак не нужен: `.github/workflows/ios-client.yml` собирает всё на облачном Маке
GitHub при каждом пуше в `ios/` и выкладывает **неподписанный**
`YgolekVPN-unsigned.ipa` во вкладку Actions → запуск → Artifacts.

Установка на iPhone:

1. Скачай `YgolekVPN-unsigned.ipa` (артефакт приходит в zip — распакуй).
2. Открой его в ESign / Feather / Scarlet и подпиши своим сертификатом
   (`.p12` + `.mobileprovision`). Bundle id менять не нужно — в проекте уже
   стоит `app.vanilla7419.emerald5335`, как в профиле.
3. Установи, открой, войди через бота и нажми кнопку подключения. При первом
   подключении iOS спросит разрешение добавить конфигурацию VPN — разреши.

Ключи подписи (`.p12`, `.mobileprovision`) в репозиторий не кладём — папка
`cert/` в `.gitignore`.
