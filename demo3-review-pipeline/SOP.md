# 🎤 SOP · Demo 3 现场 5 步操作脚本

> **总时长**：8 分钟（含话术）+ 2 分钟兜底缓冲
> **演示人**：FDE / Solution Architect
> **环境**：VS Code + GitHub Copilot (Business/Enterprise) + 本仓库 `demo3-review-pipeline/`
> **现场要求**：3 个 Copilot Chat 窗口（Step 4 需要同时开）

---

## 演示前 30 秒预热（开 demo 前做）

1. VS Code 已经 `Open Folder` 到 `demo3-review-pipeline/`
2. 终端预先跑过一次：
   ```bash
   npm install && npm test
   ```
   留在终端可见，证明仓库已就绪
3. 打开 3 个文件页签：
   - `ISSUE.md`（左）
   - `src/moderation.js`（中）
   - `tests/moderation.test.js`（右）
4. 打开 1 个 Copilot Chat（Step 1-3 用），预留 Step 4 再开 2 个

---

## ⏱ Step 1 · 设计阶段（90 秒）

### 输入 prompt（直接复制粘贴到 Copilot Chat）

```text
/design-feature

feature_name: 学生录音方言混入与低俗词识别
user_story: |
  作为内容审核运营,
  我希望在学生上传配音后:
  - 自动检测录音中的方言混入比例 (粤语/四川话/东北话等)
  - 自动识别低俗词 (维护一个 200 词的初始词库)
  - 输出风险等级: PASS / WARN / BLOCK 并给出可读理由
  验收: REST API POST /api/moderate, 输入 transcript + audio_meta, 返回 JSON 决策

请把 ISSUE.md 作为完整上下文一并阅读。先调 @architect 出技术设计。
```

### 预期 agent

- `@product-reviewer` 先快速复核 user story（5-10 秒）
- `@architect` 输出：
  1. ASCII 数据流图
  2. API 表格（Method / Path / Request / Response / Errors）
  3. 边界用例清单（空 / 超长 / 全方言 / 全低俗词）
  4. 测试策略矩阵（unit / integration / e2e × 优先级）

### 演示话术（边等输出边讲）

> "注意我没让 Copilot 直接写代码——我说的是 `/design-feature`。这是一个 prompt 模板，
> 内置了我们的设计流程：先 product 复核，再 architect 出图。
> Copilot 不是'帮我写'，它是'按我们公司的工程流程走'。"

> "现在它出的 ASCII 图、API 表、边界用例——这些就是我们工程师 onboarding 第一周
> 要学的输出标准。10 个 agent 把这些标准固化下来了。"

### ✅ 完成信号

聊天窗口出现 `## Architecture Overview` 标题 + ASCII 图。

### 🆘 兜底

如果 90 秒内没出完整设计 → 切换到 **`fallback/01-architect-output.md`**，
口播："这是我们昨晚跑同样 prompt 的输出，我们对照看一下。"

---

## ⏱ Step 2 · 实现阶段（90 秒）

### 输入 prompt

在同一个 Chat 窗口（带着 Step 1 的设计上下文），切到 **Agent 模式**（齿轮图标 → Agent），然后输入：

```text
按上面 @architect 的设计实现 src/moderation.js。要求：
1. 函数式分层：validateInput / detectProfanity / detectDialectMix / decide / moderate
2. 阈值常量化（避免 magic number）
3. 每个函数加 JSDoc
4. 响应体不回显原始词库词条（只给计数）
5. 同步更新 tests/moderation.test.js，至少覆盖 PASS / WARN / BLOCK 三档各 1 条

参考 .github/copilot-instructions.md 的项目规范。
```

### 预期 agent

Copilot Agent 模式会：
1. 读 `src/moderation.js`（已有骨架）
2. 读 `.github/copilot-instructions.md`（自动遵守规范）
3. 编辑 `src/moderation.js` + `src/lexicon.js` + `tests/moderation.test.js`
4. 调出 terminal 跑 `npm test`（如果允许 auto-run）

### 演示话术

> "看左边的文件树——Copilot 自己在改 3 个文件：moderation.js, lexicon.js, 测试。
> 这就是 Agent 模式：它能跨文件编辑、能自己跑命令、能根据测试结果回头修代码。"

> "注意它没有装新的 npm 包——因为我们在 `.github/copilot-instructions.md` 里写了
> `不要在未经确认的情况下安装新的 npm 包`。这就是规则倒灌。"

### ✅ 完成信号

`src/moderation.js` 有改动 + 终端跑 `npm test` 出现 `# pass N`。

### 🆘 兜底

如果 Copilot 卡住或编辑失败 → 直接 `git diff src/moderation.js` 让客户看预填的实现，
然后打开 **`fallback/02-agent-code.md`** 讲："这是 Copilot 完成后的等效代码"。

---

## ⏱ Step 3 · 测试加强（60 秒）

### 输入 prompt

```text
@test-engineer 请基于 src/moderation.js 当前实现，补全 tests/moderation.test.js：

1. 对 detectProfanity / detectDialectMix / decide 三个函数分别加单元测试
2. 对 PASS / WARN / BLOCK 三档分别覆盖等价类（每档至少 3 条）
3. 加边界用例：
   - 4000 字符（恰好上限）
   - 4001 字符（超限）
   - 含 emoji / 全角空格 / 多语种混合
4. 加安全测试：响应里绝对不出现原始词库词条

只输出新增的 test 代码，不要重复已有用例。
```

### 预期 agent

`@test-engineer` 会：
- 列出新增用例的 **Test Plan 表格**（用例 / 输入 / 期望）
- 输出可直接粘贴的 `tests/moderation.test.js` 补丁

### 然后跑测试

```bash
npm test
```

预期：`# pass 18+`（从 9 涨到 18 以上）

### 演示话术

> "@test-engineer 是 10 个 agent 里专门做测试的。注意它不会去改业务代码——
> 这就是 `Boundaries` 段在 .md 里写的角色边界。"

> "等价类 + 边界 + 安全——这三类用例是企业级测试的最低标准。
> 一个 prompt 让 Copilot 按这个标准来，而不是随便写几个 happy path。"

### ✅ 完成信号

终端 `# pass` 数字明显增加。

### 🆘 兜底

如果新测试有红 → 直接打开 **`fallback/03-test-output.md`**，讲："这是预跑过的输出，
现场我们一会儿单独修。" 不要在客户面前 debug。

---

## ⏱ Step 4 · 并行三视角评审（120 秒 · 高光时刻 🌟）

### 操作

**现在打开第 2 和第 3 个 Copilot Chat 窗口**（Ctrl/Cmd + Shift + I 三次）。

把下面 3 段 prompt **分别贴到 3 个窗口**，**几乎同时**按回车：

#### 窗口 1（已存在的 chat）→ 代码评审

```text
@code-reviewer 请评审 src/moderation.js 和 src/app.js。

关注：
- 函数职责单一性
- DRY 违反
- 错误处理完整性
- JSDoc 完整性
- 命名是否表达业务含义

按 Findings Table 格式输出，并给最终 Recommendation。
```

#### 窗口 2 → 红队

```text
@red-team 请尝试攻击 src/moderation.js 的 POST /api/moderate：

攻击向量包括但不限于：
1. 方言 Unicode 同形字（如把"巴适"写成"巴適"）
2. 超长 transcript 接近 4000 字符的 ReDoS 触发
3. 词库 bypass：在低俗词之间插入零宽空格
4. JSON payload 滥用：嵌套对象 / 超大 audio_meta
5. 大小写 + 全角变体绕过

输出 PoC 表格 + 建议 fix。
```

#### 窗口 3 → 安全评审

```text
@security-reviewer 请安全评审 src/moderation.js 和 src/app.js。

关注：
- 输入校验完整性（transcript 长度、类型、charset）
- 词库泄漏：日志 / 响应体 / 错误信息里是否会泄漏敏感词
- ReDoS：String.includes 是安全的，但有没有正则隐患
- Stack trace 泄漏
- JSON parse 拒绝服务

按 Severity (Critical/High/Medium/Low) 排序输出 Findings Table。
```

### 演示话术（边等输出边讲，这是高光时刻）

> "三个窗口同时跑——这就是多 agent 流水线的核心价值。原来 code review 是
> 一个工程师 review，一两天后另一个工程师再 review security——串行。"

> "现在 30 秒内拿到 3 个不同视角的报告，而且是 3 个 **专业角色** 的报告，
> 不是 3 个同质的 LLM 输出。"

> "看 red-team 的攻击向量——同形字、零宽空格、ReDoS——
> 这些是真实安全工程师的 checklist。我们把这个 checklist 固化进了 agent 定义。"

### ✅ 完成信号

3 个窗口都出现 `Findings Table` 或 `Severity` 表格。

### 🆘 兜底

如果有窗口卡住 → 打开 **`fallback/04-review-reports.md`**，说："这是我们昨晚预跑的 3 份报告，
看一下他们关注的角度完全不同。"

---

## ⏱ Step 5 · 发布工程（60 秒）

### 输入 prompt（在任意一个 chat 窗口）

```text
/ship-release

version_type: minor
release_notes: |
  ### Added
  - POST /api/moderate: 学生录音三档风险决策 (PASS/WARN/BLOCK)
  - 方言混入检测: 粤语/四川话/东北话 mock 关键词命中
  - 低俗词词库: 内置 200 条初始词库, 不在响应回显
  ### Changed
  - 校验 transcript 长度上限 4000 字符, 超长返回 400
  ### Security
  - 修复 @red-team 发现的零宽空格 bypass (合并自 Step 4)

请 @release-engineer 出：
1. 完整的 CHANGELOG.md 新版段落
2. release notes (含 Migration Notes / Rollback Steps)
3. release PR 描述模板（含审核运营 sign-off checkbox）

注意：本次 demo 不要真的执行 git commit / npm version。
```

### 预期 agent

`@release-engineer` 会按 ship-release prompt 模板，依次输出：
1. Pre-flight 检查清单（要求看 `npm test` 输出）
2. `CHANGELOG.md` 待追加段落
3. release notes 完整 markdown
4. PR 描述（含 checklist）

### 演示话术

> "最后一步——发布。注意 release-engineer 干的不是 '帮我 commit'，
> 它是出一个 **发布检查清单 + CHANGELOG + release notes + PR 模板**。"

> "为什么不让它真的 commit？因为我们在 copilot-instructions.md 写了
> `绝不 force-push 到 main`、`提交前必须 npm test 通过`——
> 这些是我们企业的发布纪律。Copilot 尊重这些纪律。"

> "8 分钟，5 步——从一个 issue 到一个可发布的 PR。这就是多 agent 流水线。"

### ✅ 完成信号

聊天窗口出现 `## [0.2.0] - 2026-XX-XX` 风格的 CHANGELOG 段落。

### 🆘 兜底

打开 **`fallback/05-release-notes.md`**，"这是预生成的完整版本，PR 模板可以直接用"。

---

## 📊 5 步速览卡（贴在显示器边上）

| Step | 时间 | Agent | 输入要点 | 完成信号 | 兜底文件 |
|---|---|---|---|---|---|
| 1 | 90s | `@architect` | `/design-feature` + ISSUE | ASCII 图 + API 表 | `01-architect-output.md` |
| 2 | 90s | Agent Mode | "按设计实现" | `src/moderation.js` 改动 | `02-agent-code.md` |
| 3 | 60s | `@test-engineer` | "补 PASS/WARN/BLOCK 等价类" | `# pass` 数字增加 | `03-test-output.md` |
| 4 | 120s | `@code-reviewer` + `@red-team` + `@security-reviewer` | 3 窗口并行 | 3 份 Findings Table | `04-review-reports.md` |
| 5 | 60s | `@release-engineer` | `/ship-release` | CHANGELOG 段落 | `05-release-notes.md` |

总时长 7 分钟，留 1 分钟 Q&A 缓冲。

---

## 🎯 演示后的关键 takeaway（30 秒收尾）

> "今天看到的不是 5 个 prompt——是 **5 个工程角色** 的协作。
> 真正的价值不是 Copilot 写代码快，而是它能按我们公司的工程标准、
> 按我们的安全规则、按我们的发布纪律来做事。
>
> 你们仓库里加一个 `.github/agents/` 目录、写几个 `.md`，
> 整个团队的工程文化就被 Copilot 复制 N 倍。"
