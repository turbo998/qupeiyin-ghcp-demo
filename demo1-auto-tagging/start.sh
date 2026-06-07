#!/usr/bin/env bash
# ============================================================
# Demo 1 - 一键启动脚本
# 用法:
#   ./start.sh              # 在线模式 (调 GitHub Copilot)
#   OFFLINE=1 ./start.sh    # 离线兜底模式 (现场断网用)
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# === LLM 路由配置 (LiteLLM → GitHub Copilot) ===
export LITELLM_BASE_URL="${LITELLM_BASE_URL:-https://api.githubcopilot.com}"
export DEFAULT_MODEL="${DEFAULT_MODEL:-claude-opus-4.8}"
export FALLBACK_MODEL="${FALLBACK_MODEL:-gpt-5.5}"

# === 数据路径 ===
export MOCK_DATA_DIR="${MOCK_DATA_DIR:-$SCRIPT_DIR/../mock-data}"
export RESULTS_DB="${RESULTS_DB:-$SCRIPT_DIR/data/results.db}"

# === 离线兜底开关 ===
export OFFLINE="${OFFLINE:-0}"

if [ "$OFFLINE" = "1" ]; then
  echo "🛟 OFFLINE 模式: 不联网, 直接读 ideal_tags.json 作为返回"
else
  echo "🌐 在线模式: 调 $LITELLM_BASE_URL ($DEFAULT_MODEL)"
fi

echo "📊 数据库: $RESULTS_DB"
echo "🚀 启动 Streamlit (端口 8501)..."
echo "   浏览器打开: http://localhost:8501"
echo ""

# 选择能 import streamlit 的 python 解释器
PY_BIN=""
for candidate in python3 /usr/bin/python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
     && "$candidate" -c "import streamlit" >/dev/null 2>&1; then
    PY_BIN="$candidate"
    break
  fi
done

if [ -n "$PY_BIN" ]; then
  echo "🐍 使用 Python 解释器: $PY_BIN"
  exec "$PY_BIN" -m streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
elif command -v streamlit >/dev/null 2>&1; then
  echo "🐍 使用 streamlit CLI"
  exec streamlit run app.py \
    --server.port 8501 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --browser.gatherUsageStats false
else
  echo "❌ 找不到能 import streamlit 的 Python, 请先跑 ./setup.sh" >&2
  exit 1
fi
