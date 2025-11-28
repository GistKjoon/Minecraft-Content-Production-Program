#!/bin/bash
# 더블클릭 한 번으로 의존성 설치 후 GUI 실행
set -euo pipefail
cd "$(dirname "$0")"

BREW_BIN="$(command -v brew || true)"
if [[ -z "$BREW_BIN" ]]; then
  echo "❌ Homebrew가 필요합니다. https://brew.sh 에서 설치 후 다시 실행하세요."
  exit 1
fi

PY_BIN="/opt/homebrew/bin/python3"
if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="$(command -v python3 || true)"
fi
if [[ -z "$PY_BIN" ]]; then
  echo "❌ python3 실행 파일을 찾지 못했습니다."
  exit 1
fi

echo "🔧 python-tk@3.13 설치 여부 확인…"
if ! brew list --versions python-tk@3.13 >/dev/null 2>&1; then
  brew install python-tk@3.13
else
  echo "✔︎ 이미 설치됨"
fi

echo "📦 pip 최신화…"
"$PY_BIN" -m pip install --upgrade pip

echo "✅ Tkinter 확인…"
"$PY_BIN" - <<'PY'
import sys
try:
    import tkinter as tk  # noqa: F401
    print("Tkinter import 성공, TkVersion:", tk.TkVersion)
except Exception as e:
    print("Tkinter import 실패:", e, file=sys.stderr)
    sys.exit(1)
PY

# 선택: nbtlib이 있으면 구조 NBT 읽기 기능이 향상됩니다.
if ! "$PY_BIN" -c "import nbtlib" >/dev/null 2>&1; then
  echo "🔎 nbtlib 미설치 — 구조 NBT 디버그 기능을 쓰려면 'pip install nbtlib' 실행을 고려하세요."
fi

echo "🚀 Minecraft 제작 도우미 실행 중…"
exec "$PY_BIN" main.py
