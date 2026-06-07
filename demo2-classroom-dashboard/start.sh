#!/usr/bin/env bash
# start.sh - 一键启动 uvicorn (端口 8000)
# 用法: ./start.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

# 兜底：如果 data/classroom.db 不存在则跑 seed
if [ ! -f "data/classroom.db" ]; then
  echo "⚠️  data/classroom.db 不存在，先生成 mock 数据..."
  python3 seed.py
fi

echo "============================================="
echo " 🎬 趣配音 班级作业看板"
echo "    访问 → http://localhost:${PORT}"
echo "    API  → http://localhost:${PORT}/docs"
echo "    停止 → Ctrl+C"
echo "============================================="

exec python3 -m uvicorn main:app --host "$HOST" --port "$PORT"
