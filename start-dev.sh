#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 실행 대상 스크립트 절대경로를 고정한다.
DEVCTL="$SCRIPT_DIR/devctl.py"

if [[ ! -f "$DEVCTL" ]]; then
  # 번역: devctl.py 파일을 찾을 수 없습니다.
  echo "[ERROR] devctl.py was not found: $DEVCTL"
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  echo "[RUN] python3 \"$DEVCTL\" up"
  exec python3 "$DEVCTL" up
fi

if command -v python >/dev/null 2>&1; then
  echo "[RUN] python \"$DEVCTL\" up"
  exec python "$DEVCTL" up
fi

# 번역: Python 3가 설치되어 있지 않습니다. 설치 후 다시 실행하세요.
echo "[ERROR] Python 3 is not installed. Install Python 3 and run again."
exit 1
