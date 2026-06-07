#!/usr/bin/env bash
# setup.sh - 一键安装依赖 + 生成 mock 数据
# 用法: ./setup.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================="
echo " 🎬 趣配音 班级作业看板 · 一键 setup"
echo "============================================="

# 1. Python 检查
if ! command -v python3 >/dev/null 2>&1; then
  echo "❌ 未检测到 python3，请先安装 Python 3.10+" >&2
  exit 1
fi
PYV="$(python3 -c 'import sys; print("%d.%d"%sys.version_info[:2])')"
echo "✅ Python $PYV"

# 2. 装依赖（用户级 pip，避免 sudo）
echo "📦 安装依赖 (pip --user) ..."
python3 -m pip install --user -r requirements.txt --quiet || {
  echo "⚠️  --user 失败，回退 pip install"
  python3 -m pip install -r requirements.txt --quiet
}

# 3. 跑 seed 生成数据库
echo "🌱 生成 mock 数据 (seed=42) ..."
python3 seed.py

# 4. 健康提示
echo ""
echo "============================================="
echo "✅ Setup 完成！下一步:"
echo "   ./start.sh         # 启动服务 (端口 8000)"
echo "   浏览器打开 http://localhost:8000"
echo "============================================="
