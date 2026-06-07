# 🎬 趣配音 × GitHub Copilot 60 分钟客户交流 Demo 包

> 面向业务部门 + IT 部门的 1 小时技术交流，包含 3 个可现场运行的 demo + PPT + 讲师手卡。

## 📦 Demo 总览

| # | 名称 | 时长 | 受众 | 技术栈 |
|---|---|---|---|---|
| 1 | 配音素材自动打标签 | 12 min | 业务（教研/运营） | Streamlit + LiteLLM + SQLite |
| 2 | 班级作业看板 | 10 min | 业务（教研/管理） | FastAPI + SQLite + ECharts |
| 3 | 审核服务多 Agent 流水线 | 8 min | IT（研发/架构） | Node.js + 5 个 Copilot Agent |

## 🚀 5 分钟现场启动

```bash
# 一次启动所有 3 个 demo（端口 8501 / 8000 / 3000）
./start-all.sh
```

启动完后浏览器打开：
- http://localhost:8501  → Demo 1 打标签 UI
- http://localhost:8000  → Demo 2 班级看板
- VS Code 打开 demo3-review-pipeline/ → Demo 3 跑 Agent

## 🖼 17 页讲师 PPT

```bash
cd docs && python3 -m http.server 8765
# 打开 http://localhost:8765/qupeiyin-ghcp-deck.html
```

键盘操作：`←` `→` 翻页 · `Home` `End` 跳首末 · `Ctrl+P` 打印 PDF。

PPT 结构（17 页）：封面 → 60min 概览 → 5 痛点 → Copilot 3 跃迁 → AI-DLC → 为什么 GHCP → Demo1 bridge + 复盘 → Harness 3 层 → 10 Agents → FDE → 6 Prompts → Demo2/Demo3 → 三个落地数字 → 90 天路线图 → Q&A。

风格：MS Azure Blue (#0078D4) + 趣配音橙红 (#FF6B35) 双主色。

## 📁 目录结构

```
.
├── demo1-auto-tagging/         # 配音素材自动打标签
├── demo2-classroom-dashboard/  # 班级作业看板
├── demo3-review-pipeline/      # 多 Agent 审核流水线
├── mock-data/                  # 公开英语素材 + 字幕（10 条）
├── docs/                       # PPT + 客户带走资料
├── speaker-notes/              # 讲师手卡
└── start-all.sh                # 一键启动
```

## 🎯 60 分钟时间表

| 时段 | 内容 |
|---|---|
| 0-5  | 开场：5 个痛点 × Copilot 精准回应 |
| 5-13 | Part 1：Copilot 三跃迁 + AI-DLC |
| **13-25** | 🔥 **Demo 1**：素材自动打标签 |
| 25-32 | 揭秘：Harness 三层模型 |
| **32-42** | 🔥 **Demo 2**：班级作业看板 |
| 42-48 | 揭秘：10 Agent + FDE 机制 |
| **48-56** | 🔥 **Demo 3**：审核服务流水线 |
| 56-60 | 落地路线图 + POC 提议 |

## 🛠 环境要求

- VS Code + GitHub Copilot (Business/Enterprise)
- Node.js 18+
- Python 3.10+ with `uv` 或 `pip`
- 浏览器 (Chrome/Edge)

详细安装见各 demo 的 README。
