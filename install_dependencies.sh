#!/usr/bin/env bash

# 간단한 설치 스크립트: Homebrew로 Python 3.13 + Tk 인터페이스 설치
# 사용법: bash install_dependencies.sh

set -euo pipefail

if ! command -v brew >/dev/null 2>&1; then
  echo "❌ Homebrew가 필요합니다. https://brew.sh 에서 설치 후 다시 실행하세요."
  exit 1
fi

echo "🔧 python-tk@3.13 설치 (python@3.13, tcl-tk 포함)…"
brew install python-tk@3.13

echo "📦 pip 최신화…"
/opt/homebrew/bin/python3 -m pip install --upgrade pip

echo "✅ Tkinter 확인…"
/opt/homebrew/bin/python3 - <<'PY'
import tkinter as tk
print("Tkinter import 성공, TkVersion:", tk.TkVersion)
PY

echo ""
echo "완료! 이제 'python3 main.py' 로 GUI를 실행해 보세요."
