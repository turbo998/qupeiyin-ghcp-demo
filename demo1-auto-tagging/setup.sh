#!/usr/bin/env bash
# ============================================================
# Demo 1 - 配音素材自动打标签 · 一键安装脚本
# 用法: ./setup.sh
# ============================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 趣配音 Demo 1 - 环境安装"
echo "==============================================="

# 检测 Python
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 未检测到 python3, 请先安装 Python 3.10+" >&2
  exit 1
fi
PY_VER=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo "✅ Python 版本: $PY_VER"

# 优先用 uv, 没有就用 pip --user
if command -v uv >/dev/null 2>&1; then
  echo "📦 使用 uv 安装依赖..."
  uv pip install --system -r requirements.txt || uv pip install -r requirements.txt
else
  echo "📦 使用 pip --user 安装依赖..."
  python3 -m pip install --user -r requirements.txt
fi

# 准备 data 目录
mkdir -p data
echo "✅ data/ 目录就绪 (results.db 首次启动自动生成)"

# 检测 GitHub Copilot token
if [ -f "$HOME/.config/gh/hosts.yml" ]; then
  echo "✅ 检测到 GitHub Copilot token: ~/.config/gh/hosts.yml"
else
  echo "⚠️  未检测到 ~/.config/gh/hosts.yml, 在线模式将无法使用"
  echo "   现场演示请用 OFFLINE=1 兜底"
fi

echo ""
echo "🎉 安装完成! 启动方式:"
echo "   ./start.sh           # 在线模式 (调 GitHub Copilot)"
echo "   OFFLINE=1 ./start.sh # 离线兜底模式 (读 ideal_tags.json)"
