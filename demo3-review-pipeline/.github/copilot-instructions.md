# 趣配音 · 内容审核服务 — 项目工程规范

> 本规范适用于「趣配音 K12 英语配音学习平台」的 **内容审核服务 (Moderation Service)**。
> 服务负责对学生上传的配音 (transcript + audio_meta) 进行方言混入识别、低俗词识别，并输出风险等级 PASS / WARN / BLOCK。

## 业务上下文

- **业务方**：趣配音 K12 英语配音学习平台
- **服务定位**：内容安全侧的实时审核 API，被「学生上传配音」「教师批阅」「素材入库」三条链路调用。
- **核心 API**：`POST /api/moderate`，输入 `{ transcript, audio_meta }`，输出 `{ decision, risk_level, reasons, evidence }`。
- **合规要求**：未成年人内容，必须保守 — 宁可误报为 WARN，不可漏判低俗词。
- **下游消费方**：审核工作台（人工复核 WARN）、自动拦截器（BLOCK）、数据看板。

## Language & Style

- 所有代码使用 **JavaScript (CommonJS)**，不引入 TypeScript。
- 使用 **Express.js** 作为 HTTP 框架，遵循项目里已有的 `src/server.js` / `src/moderation.js` 分层。
- 测试一律使用 **`node:test` + `node:assert/strict`**，不要引入 Jest / Mocha / Chai。

## Code Rules

- 新增 API endpoint **必须**配套单元测试 (`tests/*.test.js`)。
- 输入校验错误统一返回 `HTTP 400`，body 形如 `{ "error": "..." }`。
- **不要**在未经确认的情况下安装新的 npm 包；本 demo 只允许 `express` 一个生产依赖。
- 函数保持精简 (< 30 行)；模块单一职责。
- 变量命名使用有业务含义的英文短语，如 `dialectScore`、`profanityHits`，避免 `x`、`tmp`。

## Domain Rules — 审核业务

- **risk_level 三档**：`PASS` / `WARN` / `BLOCK`。任何输出必须落到这三档其中之一。
- **decision 字段** 必须带 `reasons: string[]`，每条 reason 是面向运营的人类可读中文。
- **词库 (profanity lexicon)** 通过模块常量维护，初始 200 词级别，禁止把词库直接打印进日志或返回体。
- **方言检测** 在 demo 中是 mock 实现（基于 transcript 关键词命中），后续会替换为模型推理 — 接口必须保持稳定。
- **音频元数据** (`audio_meta.duration_sec`, `audio_meta.sample_rate` 等) 即使当前未使用，也要透传并保留在响应中，便于后续审计。

## Git & PR

- Commit 信息遵循 `<type>: <description>`，例如 `feat: add dialect mix detector`。
- PR 描述四段式：**Problem / Solution / Test Coverage / Verification Steps**。

## Security

- **绝不**在 API 响应里暴露 stack trace。
- 所有 user input (`transcript`) 在进入业务逻辑前做长度校验（建议 ≤ 4000 字符）。
- 词库文件视为敏感配置 — 不要在日志、监控、对外响应里原样回显敏感词。
- 使用项目已有的 `ValidationError` 类抛出已知错误，由 Express middleware 统一转 400。

## Core Principles

These principles are adapted from the gstack ETHOS methodology:

1. **Completeness First (完整性优先)** — 审核服务漏判一次低俗词的代价远高于多一次 WARN。优先把所有边界条件兜住。
2. **Search Before Building** — 先检查 `src/moderation.js` 里有没有已有的检测函数可以复用，再决定是否新增。
3. **User Sovereignty** — Copilot Agent 给建议，但最终是否上线由审核运营 + 工程师拍板。

## Safety Guardrails

- **绝不删除** `mock-data/`、`.github/agents/`、`.github/prompts/` 下的任何文件。
- **绝不** force-push 到 `main`。
- **绝不修改** `.env` 与任何 credential 文件。
- 提交前**必须** `npm test` 通过。

## Code Quality Standards

- 每个 exported 函数必须有 **JSDoc**，包含 `@param` `@returns` `@throws`。
- **不允许 magic number** — 例如 BLOCK 阈值用 `const BLOCK_THRESHOLD = 3`。
- 错误信息要 **actionable** — 告诉调用方哪里错了 + 怎么修。例如 `"transcript 不能为空，请传入 1-4000 字符的字符串"`。
- 业务代码里 **不要 `console.log`**；调试日志走 logger 抽象（demo 阶段允许 `console.warn`，但要带前缀 `[moderation]`）。

## Agent Collaboration Protocol

本仓库内置 10 个 GitHub Copilot Agent (`.github/agents/*.md`)。在 Copilot Chat 中通过 `@agent-name` 调用。

| Agent | 在审核服务里的典型用途 |
|---|---|
| `@architect` | 给方言识别 + 词库加载设计数据流和 API 契约 |
| `@code-reviewer` | review `src/moderation.js` 的可读性、错误处理 |
| `@security-reviewer` | 查输入校验、词库泄漏、ReDoS 风险 |
| `@red-team` | 用方言变体 / Unicode 同形字 / 超长 transcript 攻击 |
| `@test-engineer` | 补全 PASS / WARN / BLOCK 三档的等价类用例 |
| `@performance-engineer` | 评估 4000 字 transcript 的延迟 / 内存 |
| `@investigator` | 现场出 bug 时复现 + 定位 |
| `@release-engineer` | 出 CHANGELOG、release notes、发布检查清单 |
| `@product-reviewer` | 评估 PASS/WARN/BLOCK 三档的产品合理性 |
| `@doc-writer` | 出审核运营手册 / API 文档 |

协作守则：
- 每个 agent 有 **明确的角色边界** — 尊重它，不要越权。Security 问题让 `@security-reviewer` 出口径。
- **不确定时**向用户确认，不要凭空假设审核词库的范围。
- 跨 agent 引用使用 `@mention`（例：`@code-reviewer 注意 @security-reviewer 已经标记的 ReDoS 风险点`）。
