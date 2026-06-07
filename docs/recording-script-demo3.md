# 🎬 录屏脚本 · Demo 3 · 审核服务多 Agent 流水线 (90 秒)

> **用途**：现场断网 / Copilot 抽风时直接播放本视频兜底
> **录制工具建议**：OBS / QuickTime + 麦克风 (单声道 48kHz 即可)
> **风格基调**：亲切 + 专业，像 FDE 在跟客户研发负责人对屏讲解
> **核心卖点**：45-75 秒的「三 Agent 并行评审」是这条流水线最炸场的一段

---

## ⏱ 总时间轴

| 段 | 时间 | 标题 | 画面 | 旁白长度 |
|---|---|---|---|---|
| ① | 0-15s | 展示 Issue | `ISSUE.md` 全屏 | 约 38 字 |
| ② | 15-30s | @architect | Chat 窗口 → ASCII 图 + API 表 | 约 38 字 |
| ③ | 30-45s | Agent 生成代码 | 文件树跳动 → `moderation.js` diff | 约 38 字 |
| ④ | 45-75s | 三 Agent 并行评审 🌟 | 三窗并排 → 3 张 Findings Table | 约 80 字 |
| ⑤ | 75-90s | release | `@release-engineer` 出 CHANGELOG | 约 40 字 |

---

## ① 0-15s · 展示 Issue

**画面**
- VS Code 全屏，打开 `demo3-review-pipeline/ISSUE.md`
- 镜头从文件顶部慢速滚到 "验收标准"
- 高亮关键词：**方言混入** / **低俗词** / **PASS / WARN / BLOCK**

**旁白**（语速稳，约 38 字）
> "趣配音每天 12 万条学生配音上传，其中 4% 需要人工审核。
> 这个 Issue 说的是：要做一个 API，自动判断方言混入和低俗词，输出三档风险等级。"

---

## ② 15-30s · @architect

**画面**
- 右侧 Copilot Chat 打开
- 输入框已粘好 `/design-feature` prompt，回车
- 几秒内输出：`## Architecture Overview` 标题 + ASCII 数据流图 + API 表格
- 镜头特写 API 表格 (Method / Path / Request / Response)

**旁白**（语速稍慢，约 38 字）
> "我没让 Copilot 直接写代码。我说的是 `/design-feature` —
> 先调 architect 角色出设计。看 — ASCII 数据流图、API 表、边界用例。
> 这就是我们工程师 onboarding 第一周要交的东西。"

---

## ③ 30-45s · Agent 生成代码

**画面**
- 切换 Copilot 到 **Agent 模式** (齿轮图标 → Agent)
- 输入框：「按上面 @architect 的设计实现 `src/moderation.js`」回车
- 左侧文件树跳动：`src/moderation.js` + `src/lexicon.js` + `tests/moderation.test.js` 同时被编辑
- 底部 terminal 自动跑 `npm test`，出现 `# pass 9`
- 这一段画面可加速 1.5 倍

**旁白**（语速适中，约 38 字）
> "切到 Agent 模式，让它按设计实现代码。
> 看 — 它自己在改三个文件，自己开 terminal 跑测试。
> 9 个用例全绿。这就是 Agent 模式：跨文件、自跑命令、按测试结果回头修。"

---

## ④ 45-75s · 三 Agent 并行评审 🌟 (高光段)

**画面**
- 屏幕一分为三：左 Code Review / 中 Red Team / 右 Security
- 三个 Copilot Chat 窗口几乎同时回车 (剪辑时对齐时间戳)
- 三个窗口同时往下吐内容：
  - 左：`Findings Table` 命名建议 / DRY 违反
  - 中：`PoC Table` 同形字攻击 / 零宽空格 bypass
  - 右：`Severity Table` Critical / High / Medium / Low
- 镜头从左扫到右，每个窗口停 3 秒

**旁白**（语速放慢，留呼吸，约 80 字）
> "现在是高光时刻。我同时开三个 Chat 窗口，几乎同一秒回车。
>
> 左边是 code-reviewer — 看的是代码质量。
> 中间是 red-team — 它在尝试攻击我们刚写的代码：同形字、零宽空格、超长 transcript。
> 右边是 security-reviewer — 按严重程度排序找安全隐患。
>
> 30 秒内拿到三份**完全不同视角**的评审报告。
> 原来这三件事，串行做要两天。现在并行做，半分钟。"

---

## ⑤ 75-90s · release

**画面**
- 切回单个 Chat 窗口
- 粘 `/ship-release` prompt，回车
- 输出：`## [0.2.0] - 2026-XX-XX` CHANGELOG 段落 + Release Notes + PR 描述模板
- 镜头特写 PR 描述里的 sign-off checkbox

**旁白**（语速稳，收束感，约 40 字）
> "最后一步 — release-engineer。
> 它出的不是 git commit，是一份**完整的发布清单**：CHANGELOG、release notes、PR 描述。
>
> 一个 Issue，到一个可发布的 PR。8 分钟。这就是多 Agent 流水线的样子。"

---

## 🛟 录制注意事项

- **第④段是核心**：录制前在三个 Chat 窗口里**预热**好 prompt，回车那一刻三个窗口同步开始才有冲击力
- **三窗并排**：建议用 1920×1080 录制，OBS 里布局成左 640 中 640 右 640
- **不要真的 git commit**：本视频纯展示，避免污染主分支
- **如果 red-team 输出特别长**：剪辑时只保留前 3 个 PoC，节奏更紧凑
- **结尾留 0.5 秒黑场**：让客户脑子里"8 分钟"这个数字沉淀一下
- **导出**：1080p / H.264 / 60-90 MB / 文件名 `qupeiyin-demo3-pipeline-90s.mp4`
