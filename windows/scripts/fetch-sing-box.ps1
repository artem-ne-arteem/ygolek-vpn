# Скачивает ядро sing-box (официальный релиз SagerNet) в YgolekVpn\core\sing-box.exe.
# Тот же скрипт запускает сборка в GitHub Actions. Версию меняй здесь.
param([string]$Version = "1.14.4")

$ErrorActionPreference = "Stop"
$core = Join-Path $PSScriptRoot "..\YgolekVpn\core"
New-Item -ItemType Directory -Force $core | Out-Null

$name = "sing-box-$Version-windows-amd64"
$zip = Join-Path ([IO.Path]::GetTempPath()) "$name.zip"
$extract = Join-Path ([IO.Path]::GetTempPath()) "$name-extract"
Invoke-WebRequest "https://github.com/SagerNet/sing-box/releases/download/v$Version/$name.zip" -OutFile $zip
Remove-Item -Recurse -Force $extract -ErrorAction SilentlyContinue
Expand-Archive $zip -DestinationPath $extract
Copy-Item (Join-Path $extract "$name\sing-box.exe") (Join-Path $core "sing-box.exe") -Force
Write-Host "sing-box $Version -> $core\sing-box.exe"
