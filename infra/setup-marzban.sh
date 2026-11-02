#!/usr/bin/env bash
# Ставит Docker + Marzban (панель управления Xray/VLESS-нодой) на чистый
# Ubuntu 22.04+ VPS. Гоняется один раз при поднятии новой ноды.
#
# Использование (на самом VPS, из-под root):
#   bash setup-marzban.sh <поддомен> <email-для-Let's-Encrypt>
#   пример: bash setup-marzban.sh sub.ygolek-vpn.online admin@ygolek-vpn.online
#
# ВАЖНО: поддомен должен уже указывать A-записью на IP этого сервера ДО
# запуска скрипта — иначе не пройдёт выпуск сертификата (Let's Encrypt
# проверяет домен по HTTP на 80 порту).
#
# Почему нужен домен+HTTPS, а не просто IP:порт: начиная с определённой
# версии Marzban сам отказывается слушать что-либо, кроме localhost, пока
# явно не заданы SSL-сертификаты (иначе dashboard и subscription-ссылки не
# были бы доступны снаружи вообще). Поэтому получаем сертификат Let's
# Encrypt и отдаём его самому Marzban напрямую (UVICORN_SSL_*), без внешнего
# reverse-proxy — так порт 443 остаётся полностью свободным под сам
# VLESS+Reality inbound, а панель/API работают на 8000 через HTTPS.
#
# После скрипта нужно руками:
#   1. Зайти в панель (https://<поддомен>:8000/dashboard/) и добавить
#      VLESS+Reality inbound с именем "VLESS TCP REALITY" (именно это имя
#      ждёт bot/bot/marzban/client.py и site/lib/marzban.ts). Marzban сам
#      генерирует Reality-ключи в UI при создании inbound-а.
#   2. Скопировать логин/пароль админа в bot/.env и в переменные окружения
#      сайта на Vercel (MARZBAN_ADMIN_USERNAME / MARZBAN_ADMIN_PASSWORD),
#      выставить MARZBAN_API_URL=https://<поддомен>:8000, MARZBAN_MOCK=false.

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Запусти скрипт от root (sudo bash setup-marzban.sh <домен> <email>)" >&2
  exit 1
fi

DOMAIN="${1:-}"
EMAIL="${2:-}"
if [[ -z "$DOMAIN" || -z "$EMAIL" ]]; then
  echo "Использование: bash setup-marzban.sh <поддомен> <email>" >&2
  echo "Пример: bash setup-marzban.sh sub.ygolek-vpn.online admin@ygolek-vpn.online" >&2
  exit 1
fi

echo "==> Обновляю пакеты"
apt-get update -y
apt-get upgrade -y

echo "==> Ставлю зависимости"
apt-get install -y curl socat ufw certbot

echo "==> Ставлю Docker"
if ! command -v docker &>/dev/null; then
  curl -fsSL https://get.docker.com | sh
fi

echo "==> Открываю нужные порты в файрволе"
ufw allow OpenSSH
ufw allow 80/tcp     # только для выпуска/продления Let's Encrypt сертификата
ufw allow 443/tcp    # VLESS+Reality inbound
ufw allow 8000/tcp   # Marzban dashboard/API (HTTPS)
ufw --force enable

echo "==> Выпускаю сертификат Let's Encrypt для $DOMAIN"
certbot certonly --standalone --non-interactive --agree-tos -m "$EMAIL" -d "$DOMAIN"

echo "==> Ставлю Marzban (официальный установщик)"
curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh -o /root/marzban.sh
bash /root/marzban.sh install

echo "==> Настраиваю Marzban на HTTPS через выпущенный сертификат"
sed -i '/^UVICORN_SSL_CERTFILE/d; /^UVICORN_SSL_KEYFILE/d' /opt/marzban/.env
cat >> /opt/marzban/.env <<EOF

UVICORN_SSL_CERTFILE=/etc/letsencrypt/live/$DOMAIN/fullchain.pem
UVICORN_SSL_KEYFILE=/etc/letsencrypt/live/$DOMAIN/privkey.pem
EOF

echo "==> Разрешаю Docker-контейнеру читать сертификаты Let's Encrypt"
chmod -R a+rX /etc/letsencrypt/live /etc/letsencrypt/archive

echo "==> Перезапускаю Marzban с HTTPS"
cd /opt/marzban
docker compose down
docker compose up -d

echo "==> Настраиваю автопродление сертификата (с перезапуском Marzban после)"
mkdir -p /etc/letsencrypt/renewal-hooks/deploy
cat > /etc/letsencrypt/renewal-hooks/deploy/marzban-restart.sh <<'EOF'
#!/usr/bin/env bash
cd /opt/marzban && docker compose restart
EOF
chmod +x /etc/letsencrypt/renewal-hooks/deploy/marzban-restart.sh

echo "==> Создаю первого администратора панели"
echo "Введи логин и пароль для админки Marzban (они же пойдут в bot/.env):"
docker exec -it marzban-marzban-1 marzban-cli admin create --sudo

cat <<EOF

Готово. Дальше руками:

1. Открой https://$DOMAIN:8000/dashboard/ и залогинься под созданным админом.
2. В разделе Hosts/Inbounds создай VLESS inbound с Reality на порту 443,
   назови его ровно "VLESS TCP REALITY".
3. В bot/.env и в env-переменных сайта на Vercel выстави:
     MARZBAN_MOCK=false
     MARZBAN_API_URL=https://$DOMAIN:8000
     MARZBAN_ADMIN_USERNAME=<логин из шага выше>
     MARZBAN_ADMIN_PASSWORD=<пароль из шага выше>
     MARZBAN_SUB_DOMAIN=$DOMAIN

После этого бот и сайт начнут создавать реальных пользователей и выдавать
рабочие ключи вместо mock-ссылок.
EOF
