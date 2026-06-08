#!/usr/bin/env bash
# ============================================================
# Demo 3 - 审核多 Agent 流水线 一键启动
# 用法:
#   ./start.sh           # 启动 Express @ 3000
#   ./start.sh test      # 跑 9 个测试 (node --test)
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 模式: test
if [ "${1:-}" = "test" ]; then
  echo "🧪 跑 9 个审核测试..."
  exec npm test
fi

# 依赖兜底
if [ ! -d "node_modules" ]; then
  echo "⚠️  node_modules 不存在,先 npm install..."
  npm install --omit=dev
fi

PORT="${PORT:-3000}"
echo "============================================================"
echo " 🎬 趣配音 审核服务 (Demo 3)"
echo "    访问 → http://localhost:${PORT}"
echo "    API  → POST http://localhost:${PORT}/api/moderate"
echo "    停止 → Ctrl+C"
echo "============================================================"

exec node src/server.js
