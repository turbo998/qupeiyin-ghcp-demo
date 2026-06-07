# 🎬 Demo 2 · 班级作业看板

> 趣配音 K12 英语配音学习平台 · 班级作业看板。
> 60 分钟客户现场 Demo 中 **10 分钟**实战环节，FDE 预制好，用户登录笔记本直接跑。

## 📌 一句话演示价值

> "英语老师查看 G4-3 班这周作业完成率 / 均分 / 待补做名单 / 最受欢迎素材 —— 然后客户现场提'再加一个家长打卡指标'，**30 秒**用 Copilot Agent 改完上线，传统流程要 2 周。"

---

## 🚀 快速启动 (FDE 预制 30 秒)

```bash
cd demo2-classroom-dashboard/

# 1) 一次性 setup：装依赖 + 跑 seed 生成 SQLite
./setup.sh

# 2) 启动服务（前台，Ctrl+C 退出）
./start.sh
```

打开浏览器：<http://localhost:8000>

> 端口被占？`PORT=8001 ./start.sh`

---

## ✅ 验证（启动后 30 秒自检）

```bash
# DB 已生成 & 至少 5000 条提交
sqlite3 data/classroom.db "SELECT COUNT(*) FROM submissions;"

# Health
curl -s http://localhost:8000/api/health

# KPI
curl -s http://localhost:8000/api/kpi | python3 -m json.tool

# OpenAPI 文档
open http://localhost:8000/docs
```

期望：
- `submissions` ≥ 5000（实际约 6000-7500）
- KPI 4 项数字都非 0
- 浏览器看板 4 个图均渲染，中文正常

---

## 🎤 现场口令 SOP（4 步 · 10 分钟）

| 步 | 动作 | 口令（说给客户） | 时长 |
|----|------|------------------|------|
| **1** | 浏览器已开 <http://localhost:8000> | "这是 X 学校教研主任每天打开看的看板：总学生 500，本周完成率 60%，平均分 82，10 个班 9 个活跃。" | 1 min |
| **2** | 左侧点 **G4-3**，时间切 **近 7 天** | "现在我看 4 年级 3 班这周情况。柱状图我们班高亮橙色，**完成率比全校平均低 5 个点**；待补做榜单一目了然，《Hello Song》是最受欢迎素材。" | 2 min |
| **3** | 切到 VS Code，对 Copilot Agent 说【下面 Prompt】 | "客户说：'我们家长群也在打卡，能不能加一个家长打卡参与度？'—— 看我现场让 Copilot 加。" | 30 sec 输入 |
| **4** | 等 Copilot 改完 → 浏览器刷新 → 看到新 KPI 卡 | "**30 秒**就上了一个指标。传统流程：BA 写需求 1 周、前后端排期 1 周，**2 周对比 30 秒**。这就是 AI-DLC。" | 1 min |

### 🔑 步骤 3 的 Copilot Prompt（直接复制粘）

```
在 demo2-classroom-dashboard 项目里加一个'家长打卡参与度'指标。
后端：/api/parent_checkin 已经写好（main.py 末尾），不用动。
前端：在 static/index.html 的 KPI 行追加第 5 个 kpi-card：
  - 调用 /api/parent_checkin?days=7（如果选中了班级带上 class_id）
  - 显示 checkin_rate 字段（百分比，橙色大数字）
  - 副标题写 "近 7 天 / 已绑定 {bound_rate}%"
切换班级和时间时也要刷新这个卡。改完后我会刷新浏览器。
```

> **关键**：`/api/parent_checkin` 已在 `main.py` 中实现好（扩展点），Copilot 只需改前端 1 个文件。

---

## 🆘 现场兜底（万一出问题）

| 症状 | 处理 |
|------|------|
| 端口 8000 被占 | `lsof -i:8000` 看进程 → `kill -9 PID`，或 `PORT=8001 ./start.sh` |
| 看板空白 / 图不出 | 浏览器 F12 控制台 → 多半是 `/api/*` 报错；检查 `data/classroom.db` 是否存在，`./setup.sh` 重跑 |
| ECharts CDN 加载慢 | 把 `static/index.html` 里 `cdn.jsdelivr.net` 换成 `unpkg.com/echarts@5.4.3/dist/echarts.min.js` |
| Copilot 改坏了 | `git checkout static/index.html`（提前 commit 一份基线） |
| seed 报错 | 确认 `../mock-data/materials.json` 存在（10 条） |
| 中文乱码 | 浏览器换 Chrome / Edge；终端 `export LANG=zh_CN.UTF-8` |

---

## 📂 文件结构

```
demo2-classroom-dashboard/
├── main.py                  # FastAPI 后端（含 7 个 endpoint）
├── seed.py                  # mock 数据生成 (seed=42)
├── requirements.txt         # fastapi + uvicorn
├── setup.sh                 # 一键 install + seed
├── start.sh                 # 一键启动 uvicorn
├── README.md                # 本文件
├── static/
│   └── index.html           # 单页前端 (ECharts CDN)
└── data/                    # ← 启动后自动生成
    └── classroom.db         # SQLite
```

---

## 🔌 API 一览

| Method | Path | 说明 |
|--------|------|------|
| GET | `/`                              | 看板 HTML |
| GET | `/api/health`                    | 健康检查 |
| GET | `/api/kpi`                       | 顶部 4 个 KPI |
| GET | `/api/classes`                   | 班级下拉 |
| GET | `/api/completion_rate`           | 各班完成率柱状图（`class_id` 高亮，`start`/`end` 日期） |
| GET | `/api/avg_score_trend`           | 均分趋势折线（`class_id?`、`days=7`） |
| GET | `/api/pending_students`          | 待补做名单 Top N（`class_id?`、`limit=10`） |
| GET | `/api/popular_materials`         | 最受欢迎素材饼图（`limit=5`） |
| GET | `/api/parent_checkin` 🔌 **扩展点** | 家长打卡参与度（现场加指标用） |

---

## 🎨 视觉规范

- 主背景：浅灰 `#F5F7FA`
- MSFT 蓝：`#0078D4`（按钮、柱状图基色）
- 趣配音橙：`#FF6B35`（KPI 大数字、选中状态、高亮柱）
- 中文优先字体：Segoe UI → 微软雅黑 → PingFang SC

---

## 📊 Mock 数据规模（seed=42 可复现）

| 表 | 行数 |
|----|------|
| classes | 10 |
| students | 500 |
| materials | 10 |
| assignments | 30 |
| assignment_classes | ~195 |
| **submissions** | **~6500（≥5000 达标）** |
