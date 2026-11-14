#!/usr/bin/env bash
# Собирает ядро sing-box для iOS (Libbox.xcframework) в ios/Frameworks.
# Нужны macOS, Xcode и Go 1.25+. В CI результат кэшируется по версии.
set -euo pipefail
VERSION="${1:-1.14.4}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$(mktemp -d)"

git clone --depth 1 --branch "v$VERSION" https://github.com/SagerNet/sing-box.git "$WORK/sing-box"
cd "$WORK/sing-box"
go install github.com/sagernet/gomobile/cmd/gomobile@v0.1.13
go install github.com/sagernet/gomobile/cmd/gobind@v0.1.13
export PATH="$PATH:$(go env GOPATH)/bin"
go run ./cmd/internal/build_libbox -target apple -platform ios

mkdir -p "$ROOT/Frameworks"
rm -rf "$ROOT/Frameworks/Libbox.xcframework"
mv Libbox.xcframework "$ROOT/Frameworks/"
echo "Libbox.xcframework -> $ROOT/Frameworks"
