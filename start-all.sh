#!/usr/bin/env bash
# ============================================================
# 趣配音 × GitHub Copilot Demo — 一键启动全部 3 个 demo
#
#   Demo 1 打标签    → http://localhost:8501  (Streamlit)
#   Demo 2 班级看板  → http://localhost:8000  (FastAPI)
#   Demo 3 审核服务  → http://localhost:3000  (Node / Express)
#
# 用法:
#   ./start-all.sh              # 在线模式
#   OFFLINE=1 ./start-all.sh    # Demo1 走离线兜底 (现场断网可用)
#   Ctrl+C                      # 一次性停止全部
#
# 依赖:
#   - Python: 优先用 repo 内 .venv，其次 PATH 上能 import streamlit 的 python
#             首次若都没有，会用 uv 自动建 .venv 并装依赖 (需先装 uv)
#   - Node 18+: demo3 首次会自动 npm install
#
# Windows 提示: 请在 **Git Bash** 里运行本脚本 (PATH 上的 bash 可能是 WSL，
#              看不到 Windows 侧的 .venv)。例如双击 Git Bash 后:
#                cd /c/.../qupeiyin-ghcp-demo && ./start-all.sh
# ============================================================
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

OFFLINE="${OFFLINE:-0}"

# ------------------------------------------------------------
# 选择 Python 解释器
#   1) repo 内 .venv (Windows: .venv/Scripts/python.exe, *nix: .venv/bin/python)
#   2) PATH 上能 import streamlit 的 python3 / python / py
# ------------------------------------------------------------
pick_python() {
  local cands=()
  [ -x "$ROOT/.venv/Scripts/python.exe" ] && cands+=("$ROOT/.venv/Scripts/python.exe")
  [ -x "$ROOT/.venv/bin/python" ]         && cands+=("$ROOT/.venv/bin/python")
  cands+=(python3 python py)

  local first_ok=""
  for c in "${cands[@]}"; do
    command -v "$c" >/dev/null 2>&1 || [ -x "$c" ] || continue
    "$c" -c "import sys" >/dev/null 2>&1 || continue
    if "$c" -c "import streamlit" >/dev/null 2>&1; then
      echo "$c"; return 0
    fi
    [ -z "$first_ok" ] && first_ok="$c"
  done
  [ -n "$first_ok" ] && { echo "$first_ok"; return 0; }
  return 1
}

# ------------------------------------------------------------
# 首次自动建环境: uv venv .venv (x64 CPython 3.14, arm64 机器也能装齐 wheel)
#                + uv pip install -r requirements.txt
# ------------------------------------------------------------
bootstrap_venv() {
  command -v uv >/dev/null 2>&1 || {
    echo "❌ 未装 streamlit 且未找到 uv，无法自动建环境。" >&2
    echo "   方案A: 安装 uv (https://docs.astral.sh/uv/) 后重跑本脚本" >&2
    echo "   方案B: 手动 python -m venv .venv && .venv/Scripts/pip install -r requirements.txt" >&2
    return 1
  }
  echo "🧰 首次运行：创建 .venv 并安装 Python 依赖 (uv, 约 1-2 分钟) ..."
  uv venv .venv --python 3.14 || uv venv .venv || return 1
  local venv_py="$ROOT/.venv/Scripts/python.exe"
  [ -x "$venv_py" ] || venv_py="$ROOT/.venv/bin/python"
  uv pip install --python "$venv_py" -r requirements.txt || return 1
}

PY="$(pick_python)" || {
  bootstrap_venv && PY="$(pick_python)"
}
[ -n "${PY:-}" ] || {
  echo "❌ Python 环境就绪失败，请检查上面的报错。" >&2
  exit 1
}

command -v node >/dev/null 2>&1 || {
  echo "❌ 未找到 node (需要 Node 18+)" >&2
  exit 1
}

LOG_DIR="$ROOT/.run-logs"
mkdir -p "$LOG_DIR"
PIDS=()

cleanup() {
  echo ""
  echo "🛑 停止全部 demo ..."
  for pid in "${PIDS[@]:-}"; do
    kill "$pid" >/dev/null 2>&1 || true
  done
  wait 2>/dev/null || true
  echo "✅ 已全部停止"
}
trap cleanup INT TERM EXIT

echo "============================================================"
echo " 🎬 趣配音 × GitHub Copilot — 一键启动"
echo "    Python: $PY"
if [ "$OFFLINE" = "1" ]; then
  echo "    模式:   🛟 OFFLINE (Demo1 读 ideal_tags.json, 不联网)"
else
  echo "    模式:   🌐 在线 (Demo1 调 GitHub Copilot; 断网请用 OFFLINE=1)"
fi
echo "============================================================"

# ---- Demo 1: Streamlit (8501) ----
echo "▶ [1/3] Demo1 打标签 (8501) ..."
(
  cd "$ROOT/demo1-auto-tagging"
  OFFLINE="$OFFLINE" exec "$PY" -m streamlit run app.py \
    --server.port 8501 --server.address 0.0.0.0 \
    --server.headless true --browser.gatherUsageStats false
) >"$LOG_DIR/demo1.log" 2>&1 &
PIDS+=($!)

# ---- Demo 2: FastAPI (8000) ----
echo "▶ [2/3] Demo2 班级看板 (8000) ..."
(
  cd "$ROOT/demo2-classroom-dashboard"
  if [ ! -f data/classroom.db ]; then
    echo "  ↳ 首次运行，生成 mock 数据 (seed.py) ..."
    "$PY" seed.py
  fi
  exec "$PY" -m uvicorn main:app --host 0.0.0.0 --port 8000
) >"$LOG_DIR/demo2.log" 2>&1 &
PIDS+=($!)

# ---- Demo 3: Node / Express (3000) ----
echo "▶ [3/3] Demo3 审核服务 (3000) ..."
(
  cd "$ROOT/demo3-review-pipeline"
  if [ ! -d node_modules ]; then
    echo "  ↳ 首次运行，npm install ..."
    npm install
  fi
  exec node src/server.js
) >"$LOG_DIR/demo3.log" 2>&1 &
PIDS+=($!)

echo ""
echo "⏳ 等待服务就绪 (~8s) ..."
sleep 8
echo ""
echo "============================================================"
echo "✅ 全部启动完成！浏览器打开:"
echo "   Demo 1 打标签    → http://localhost:8501"
echo "   Demo 2 班级看板  → http://localhost:8000"
echo "   Demo 3 审核服务  → http://localhost:3000"
echo ""
echo "📜 日志: $LOG_DIR/demo{1,2,3}.log"
echo "🛑 停止: 在本窗口按 Ctrl+C (一次性停止全部)"
echo "============================================================"

wait
