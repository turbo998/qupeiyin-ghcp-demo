# 🎬 Demo 1 · 配音素材自动打标签

> 趣配音 × GitHub Copilot · 60 分钟客户交流第 1 个 demo (时长 12 min)
>
> AI 5 秒完成教研老师 30 分钟的素材入库标签工作。

---

## 🚀 5 分钟启动 (FDE 预制清单)

```bash
# 1) 进入目录
cd demo1-auto-tagging

# 2) 一键装依赖 (Python 3.10+)
./setup.sh

# 3) 启动 (默认在线模式, 走 GitHub Copilot)
./start.sh
# → 浏览器自动可访问 http://localhost:8501
```

> 如果现场断网, 立刻改用：
> ```bash
> OFFLINE=1 ./start.sh
> ```

---

## 🎬 现场操作 SOP (3 步)

### 步骤 1 · 单条打标 (3 分钟) — 体现"5 秒出标签"
1. 默认进入「📝 单条打标」tab
2. 在左侧 **「快速选择样例」** 下拉里选 `The Very Hungry Caterpillar...`
3. 点 **🚀 AI 打标签** → 右侧 5 秒内弹出彩色标签卡片 (年级/题材/难度/推荐分等)

### 步骤 2 · 批量打标 (5 分钟) — 体现"批量提效"
1. 切到「📦 批量打标」tab
2. 勾选 **「直接用 mock-data/materials.json」**, 右侧自动加载 10 条
3. 点 **🚀 批量打标 (10 条)** → 进度条 30 秒内跑完, 表格全展示
4. 点 **⬇️ 下载结果 CSV** → 演示"教研可直接导出"

### 步骤 3 · 沉淀演示 (4 分钟) — 体现"教研知识资产化"
1. 切到「📐 .prompt.md 教研沉淀」tab
2. 现场展示 prompt 模板, 强调:
   - "8 位教研老师的判定规则全在这一个文件里"
   - "git 版本管理, 谁改了一目了然"
   - "老师走了, 知识不走"
3. (可选) 切到「📜 历史记录」tab, 展示 SQLite 累计的全量结果

---

## 🛟 万一现场出问题怎么办？

| 故障现象 | 兜底动作 | 预计恢复 |
|---|---|---|
| 网络不通 / Copilot API 超时 | 关掉 streamlit, 改用 `OFFLINE=1 ./start.sh` | 30 秒 |
| `~/.config/gh/hosts.yml` 没 token | 程序自动降级到 offline 兜底, **不会报错**, 模型栏会显示 `fallback-no-token` | 0 秒, 透明 |
| LLM 返回非 JSON | 程序内置容错解析 + 启发式兜底, 仍能出卡片 | 0 秒, 透明 |
| Streamlit 装不上 | `python3 -m pip install --user streamlit pandas` 单独装核心包 (litellm 可选) | 1 分钟 |
| 端口 8501 被占 | `./start.sh` 改用 `streamlit run app.py --server.port 8502` | 10 秒 |
| 历史记录脏数据 | 侧边栏点 **🗑 清空历史** | 5 秒 |

> **核心保险**: `OFFLINE=1` 模式不需要任何网络、不需要 token、不需要 litellm,
> 只要 Python + streamlit + pandas 三个包就能跑通完整流程。

---

## 📁 文件清单

```
demo1-auto-tagging/
├── app.py                              # Streamlit 主程序 (~650 行)
├── requirements.txt                    # 4 个核心依赖
├── setup.sh                            # 一键装依赖
├── start.sh                            # 一键启动 (export 环境变量)
├── README.md                           # 本文件
├── prompts/
│   └── tag-material.prompt.md          # 教研沉淀的 prompt 模板
└── data/
    └── results.db                      # SQLite, 首次启动自动建表
```

---

## ⚙️ 环境变量速查

| 变量名 | 默认值 | 说明 |
|---|---|---|
| `OFFLINE` | `0` | 设 `1` 走离线 ideal_tags.json 兜底 |
| `LITELLM_BASE_URL` | `https://api.githubcopilot.com` | LLM 网关 |
| `DEFAULT_MODEL` | `claude-opus-4.8` | 主模型 |
| `FALLBACK_MODEL` | `gpt-5.5` | 兜底模型 |
| `MOCK_DATA_DIR` | `../mock-data` | 素材 + 理想标签数据目录 |
| `RESULTS_DB` | `./data/results.db` | SQLite 路径 |

---

## 🔬 技术栈

- **UI**: Streamlit 1.32+ (橙 #FF6B35 + 蓝 #0078D4 双色风)
- **LLM 路由**: LiteLLM → GitHub Copilot (`api.githubcopilot.com`)
- **存储**: SQLite (零运维, 单文件)
- **Token**: 从 `~/.config/gh/hosts.yml` 读 oauth_token
- **兜底**: ideal_tags.json (10 条 gold case) + 启发式打分

---

## ✅ 自验

```bash
python3 -m py_compile app.py    # 应无任何输出
OFFLINE=1 ./start.sh             # 浏览器打开 http://localhost:8501, 整套跑通
```
