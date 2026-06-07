# 🎬 Demo 3 · 审核服务多 Agent 流水线

> **场景**：趣配音 K12 英语配音学习平台 — 内容审核服务
> **目标**：用 5 个 GitHub Copilot Agent 在 8 分钟内走完 "需求 → 设计 → 编码 → 测试 → 评审 → 发布" 全链路
> **受众**：IT (研发负责人 / 架构师 / 平台工程)
> **时长**：现场演示 8 min（含问答 12 min）

---

## 1. 业务背景：为什么是审核服务？

趣配音每天有 ~12 万条学生配音上传，其中约 4% 触发人工复核。当前痛点：

| 痛点 | 现状 | 期望 |
|---|---|---|
| 方言混入（学生用粤语/四川话/东北话念英文） | 全靠人工抽查 | 自动算混入比例，超 15% 直接拒 |
| 低俗词识别 | 词库散落在 3 个微服务，规则不一致 | 200 词初始词库，统一三档输出 |
| 审核效率 | 人均 280 条/日 | 目标 600 条/日 |
| 决策可解释性 | "感觉不太行" | 每条 reject 必须给可读理由 |

本 demo 围绕 **POST /api/moderate** 这一个 API，演示如何用 10 个 Copilot Agent 把这条链路一次性走通。

---

## 2. 现场 5 步流程（每步 1-2 分钟）

> 💡 完整脚本（含可粘贴 prompt + 话术 + 时间）见 **[SOP.md](./SOP.md)**
> 💡 万一现场 Copilot 慢/挂，兜底素材见 **[fallback/](./fallback/)**

```
ISSUE.md (需求)
   │
   ▼
[1] /design-feature ──→ @architect           → 技术设计 + ASCII 数据流图 + API 表格
   │
   ▼
[2] Copilot Agent 模式 ──→ src/moderation.js   → 实现 + 单测脚手架
   │
   ▼
[3] @test-engineer ──→ tests/moderation.test.js → PASS / WARN / BLOCK 等价类
   │
   ▼
[4] 并行 3 个 chat 窗口:
    @code-reviewer  + @red-team  + @security-reviewer   → 3 份评审报告 (~30 秒)
   │
   ▼
[5] @release-engineer ──→ CHANGELOG.md + release notes
```

---

## 3. 仓库结构

```
demo3-review-pipeline/
├── README.md                      ← 本文件
├── ISSUE.md                       ← 客户场景化需求（输入材料）
├── SOP.md                         ← 现场 5 步操作脚本（FDE 必看）
├── package.json                   ← Express + node:test
├── src/
│   ├── server.js                  ← 端口 3000 入口
│   ├── app.js                     ← Express 路由
│   ├── moderation.js              ← 三档决策核心逻辑
│   └── lexicon.js                 ← 低俗词 + 方言关键词（mock）
├── tests/
│   └── moderation.test.js         ← 9 条单测（PASS/WARN/BLOCK + 校验 + 安全）
├── fallback/                      ← 兜底素材：5 步预期 Copilot 输出
│   ├── 01-architect-output.md
│   ├── 02-agent-code.md
│   ├── 03-test-output.md
│   ├── 04-review-reports.md       ← 含 3 份评审 (code/red-team/security)
│   └── 05-release-notes.md
└── .github/
    ├── copilot-instructions.md    ← 项目工程规范（已适配审核业务上下文）
    ├── agents/                    ← 10 个 Copilot Agent（与 lab-starter 一致）
    │   ├── architect.md
    │   ├── code-reviewer.md
    │   ├── doc-writer.md
    │   ├── investigator.md
    │   ├── performance-engineer.md
    │   ├── product-reviewer.md
    │   ├── red-team.md
    │   ├── release-engineer.md
    │   ├── security-reviewer.md
    │   └── test-engineer.md
    └── prompts/                   ← 6 个 prompt 模板（含趣配音示例）
        ├── add-endpoint.prompt.md
        ├── code-review.prompt.md
        ├── design-feature.prompt.md
        ├── fix-bug.prompt.md
        ├── investigate-issue.prompt.md
        └── ship-release.prompt.md
```

---

## 4. 5 分钟启动

```bash
cd demo3-review-pipeline
npm install        # 只装 express 一个生产依赖
npm test           # 9 条单测全绿
npm start          # http://localhost:3000
```

### 一键自测

```bash
# 健康检查
curl http://localhost:3000/health

# PASS（干净 transcript）
curl -X POST http://localhost:3000/api/moderate \
  -H 'Content-Type: application/json' \
  -d '{"transcript":"Hello, my name is Alice. I love English.","audio_meta":{"duration_sec":3.2}}'

# BLOCK（命中 3 条低俗词）
curl -X POST http://localhost:3000/api/moderate \
  -H 'Content-Type: application/json' \
  -d '{"transcript":"badword01 badword02 badword03"}'

# 400（空 transcript）
curl -X POST http://localhost:3000/api/moderate \
  -H 'Content-Type: application/json' \
  -d '{"transcript":""}'
```

---

## 5. 10 个 Agent 角色一览（本 demo 现场用到的标 ★）

| Agent | 角色 | 本 demo 用法 |
|---|---|---|
| ★ `@architect` | 工程架构师 | Step 1：出技术设计 + ASCII 图 + API 表 |
| ★ `@test-engineer` | 测试工程师 | Step 3：补 PASS/WARN/BLOCK 等价类 |
| ★ `@code-reviewer` | 代码评审 | Step 4：DRY / 可读性 / 错误处理 |
| ★ `@red-team` | 红队对抗 | Step 4：方言变体 / Unicode / 超长攻击 |
| ★ `@security-reviewer` | 安全评审 | Step 4：ReDoS / 词库泄漏 / 输入校验 |
| ★ `@release-engineer` | 发布工程 | Step 5：CHANGELOG + release notes |
| `@product-reviewer` | 产品评审 | 备用：评 PASS/WARN/BLOCK 三档合理性 |
| `@performance-engineer` | 性能工程 | 备用：评估 P95 延迟 |
| `@investigator` | 故障调查 | 备用：现场出 bug 时复现 + 定位 |
| `@doc-writer` | 文档工程 | 备用：出审核运营手册 |

---

## 6. 给客户讲什么（话术速记）

- **"一个 issue → 一个发布"**：5 分钟内走完工程闭环。
- **"10 个角色不是 10 个 prompt"**：是 10 个有 **角色边界 + 输出格式 + 协作规则** 的硬约束。
- **"并行召唤"**：第 4 步同时开 3 个 chat 窗口，30 秒拿到 3 份不同视角的评审。
- **"Copilot 不是替换工程师，是放大每个工程师的角色辐射"**：原来一个工程师能干的事，现在借 10 个 agent 同时干。

---

## 7. 现场可能被问到的问题

| Q | A |
|---|---|
| Agent 之间会不会扯皮？ | 不会。每个 agent 的 `.md` 里有明确 `Boundaries` 段。`@architect` 不写代码，`@security-reviewer` 不做架构决策。 |
| 词库怎么管理？ | 本 demo 是内置 mock；真实场景接审核运营后台的配置中心，支持灰度。`@architect` 在 Step 1 会画到图里。 |
| 方言识别真的能 work？ | 本 demo 是关键词命中。真实方案是声学模型 + ASR，但 API 契约保持一致，可平滑替换。 |
| 这套 agent 是 GitHub 原生的吗？ | `.github/agents/*.md` 是 Copilot Chat 识别的 custom agent 标准格式，企业版直接生效。 |

---

下一步：打开 **[SOP.md](./SOP.md)**，照着脚本走一遍。
