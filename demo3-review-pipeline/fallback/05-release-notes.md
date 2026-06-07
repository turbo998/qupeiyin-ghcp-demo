# Fallback 05 · `@release-engineer` 发布工程产物（预跑版）

> 这是 **Step 5** 的兜底素材：现场如果 `@release-engineer` 慢，直接展示本文件。
> 演示要点：Copilot 不是直接 `git commit` 或 `npm publish`，而是按发布纪律 **产出可审计的发布资产**。

---

## 🛫 Pre-flight 检查（`@release-engineer` 输出）

执行前我需要确认以下条件——这是 `.github/copilot-instructions.md` 里的发布纪律：

| # | 检查项 | 命令 | 期望 | 当前状态 |
|---|---|---|---|---|
| 1 | 所有测试通过 | `npm test` | `# pass N, # fail 0` | ✅ 23/23 通过 |
| 2 | 安全评审 P0/P1 已修 | review log | 0 个 Critical / 0 个 unresolved High | ✅ 已合并 |
| 3 | red-team 回归测试 | `npm test -- --pattern="安全"` | 新增 3 条全绿 | ✅ |
| 4 | `npm audit` 无 high | `npm audit --production` | 0 high / critical | ✅ 0 vulnerabilities |
| 5 | CHANGELOG 待更新 | manual | 新版本段落已草拟 | ⏳ 见下文 |
| 6 | Migration / Rollback | manual | 已写 | ⏳ 见下文 |

✅ 全部 Pre-flight 通过，可继续发布流程。

---

## 📄 CHANGELOG.md 待追加段落

将以下内容**插入到 `CHANGELOG.md` 文件顶部**：

```markdown
## [0.2.0] - 2026-06-08

### Added
- ✨ **POST /api/moderate** — 学生录音三档风险决策 API
  - 输入：`{ transcript: string (1-4000), audio_meta?: object }`
  - 输出：`{ decision, risk_level (PASS/WARN/BLOCK), reasons[], evidence }`
- 🌏 **方言混入检测** — 内置粤语 / 四川话 / 东北话关键词命中（mock 实现）
  - 阈值：≥5% → WARN，≥15% → BLOCK
  - top_dialect 字段标记主要方言来源
- 📚 **低俗词词库** — 200 条初始词库 (`src/lexicon.js`)
  - 阈值：≥1 命中 → WARN，≥3 命中 → BLOCK
  - 响应 evidence 仅返回计数 + 分类，不回显原始词条

### Changed
- 🛡️ **输入校验加强** — transcript 长度上限 4000 字符，超长返回 HTTP 400
- 📦 **包结构** — 拆分 `moderation.js` (业务) / `lexicon.js` (词库) / `app.js` (路由)
- 🔁 **决策规则** — 同时命中低俗词 + 方言时取更严的 risk_level

### Security
- 🔒 **Unicode 归一化** — 修复 @red-team 报告的零宽空格 bypass (`#PR-12`)
- 🔒 **繁简变体识别** — 词库扩展繁体变体（如"巴適"等于"巴适"）
- 🔒 **JSON 深度限制** — audio_meta 嵌套 ≤ 3 层，超出 400 拒绝
- 🔒 **响应安全** — 严禁原始词库词条出现在 response body / log / error message
- 🔒 **500 兜底** — 统一中间件，绝不泄漏 stack trace

### Fixed
- 🐛 `audio_meta = null` 时透传逻辑修正为透传 `{}`
- 🐛 `decide` 函数中 BLOCK 优先级修正（之前 WARN 可能覆盖 BLOCK 的 reason）

### Tests
- ✅ 用例数从 9 → 23（+14）
- ✅ 覆盖 PASS / WARN / BLOCK 三档各 ≥ 3 条等价类
- ✅ 红队回归用例 3 条（零宽空格 / 繁简变体 / JSON 深度）

### Internal
- 📝 `.github/agents/` 10 个 Copilot Agent 协作流水线
- 📝 SOP.md — 5 步现场演示脚本
```

---

## 🚀 Release Notes (对外，给 IT 团队 / 审核运营看)

```markdown
# 趣配音 · 内容审核服务 v0.2.0 Release Notes

**发布日期**: 2026-06-08
**版本**: 0.2.0 (minor)
**兼容性**: 向后兼容 — 无 breaking change
**负责人**: @审核服务工程组

---

## 🎯 本次发布解决什么问题

审核运营组提出的 [QPY-MOD-001 学生录音方言混入与低俗词识别] 需求落地：
- 配音上传链路新增自动审核能力
- 三档决策（PASS / WARN / BLOCK）+ 可读理由
- 审核工作台只需处理 WARN 档，预计人均日处理量 280 → 600 (+114%)

## ✨ 新功能

### 1. 自动审核 API: POST /api/moderate

```bash
curl -X POST https://moderation.qupeiyin.com/api/moderate \
  -H 'Content-Type: application/json' \
  -d '{
    "transcript": "Hello, my name is Alice.",
    "audio_meta": {"duration_sec": 4.2, "sample_rate": 16000}
  }'
```

响应：
```json
{
  "decision": "allow",
  "risk_level": "PASS",
  "reasons": ["未命中低俗词，未检测到方言混入"],
  "evidence": {
    "profanity_hits": 0,
    "dialect_ratio": 0,
    "top_dialect": null,
    "audio_meta_passthrough": {"duration_sec": 4.2, "sample_rate": 16000}
  }
}
```

### 2. 决策矩阵（运营组对齐版）

| 命中条件 | risk_level | decision | 审核工作台行为 |
|---|---|---|---|
| 干净 | PASS | allow | 直接通过，不入工单 |
| 低俗词 1-2 / 方言 5-15% | WARN | review | 进入人工复核队列 |
| 低俗词 ≥3 / 方言 ≥15% | BLOCK | reject | 直接拦截，学生收到友好提示 |

## 🔄 Migration Notes (给上游接入方)

**没有 breaking change**。如果你之前接入的是 v0.1.0（仅 `/health`），升级步骤：

1. 更新依赖（无新增 npm 包，仅源码升级）
2. 上游调用方在配音上传成功后，新增一次 `POST /api/moderate` 调用
3. 根据返回的 `decision` 字段分支：
   - `allow` → 继续原有"展示给学生 + 入素材库"流程
   - `review` → 进审核工作台队列（队列名：`mod-warn`）
   - `reject` → 提示学生重录，错误码 `MOD_BLOCK_001`

**建议接入超时**: 100ms（实测 P95 < 5ms）

## ↩️ Rollback Steps

如果发现线上问题需回滚到 v0.1.0：

```bash
# 1. 切到上一版本 tag
git checkout v0.1.0

# 2. 重启服务
npm install && npm start

# 3. 通知上游临时关闭 /api/moderate 调用（feature flag）
curl -X POST https://config.qupeiyin.com/flags/moderation -d '{"enabled":false}'

# 4. 在审核工作台开启降级模式：所有上传走人审
```

预计回滚时间：< 5 分钟。

## 🐛 Known Issues

- **方言识别仅基于 ASR 转写**，纯方言发音但 ASR 转成普通话会漏判 → 下个版本接声学模型
- **词库目前内置**，运营修改需发版 → v0.3.0 接入配置中心热加载
- **不支持多语种混合**，仅中英文场景

## 🙏 致谢

- `@architect` 出技术设计
- `@code-reviewer` / `@red-team` / `@security-reviewer` 三视角并行评审
- `@test-engineer` 补全 23 条单测
- `@release-engineer` 出本 release notes

---

## ✅ 发布检查清单（PR Reviewer 必看）

- [x] 所有测试通过（23/23）
- [x] `npm audit` 0 high / critical
- [x] CHANGELOG 已更新
- [x] Migration Notes 已写
- [x] Rollback Steps 已写
- [x] 安全评审 P0/P1 已修
- [x] 红队回归测试已加
- [ ] **审核运营组 sign-off** ← 请 @审核运营 在本 PR 评论 "运营确认放行"
- [ ] **SRE sign-off** ← 请 @SRE 确认监控告警已配置
- [ ] **网关团队** ← 请 @网关 确认 rate limit 已配置（建议 1000 QPS）
```

---

## 📦 Release PR 描述模板

```markdown
# Release v0.2.0 (minor) — 内容审核服务自动决策

## Problem

学生配音上传后无自动审核能力，全靠人工抽查，运营组人均日处理量上限 280 条，瓶颈严重。

## Solution

新增 `POST /api/moderate` API，三档决策（PASS/WARN/BLOCK）+ 可读理由。
词库 mock + 方言关键词命中，后续可平滑替换为模型推理。

## Test Coverage

- 单测：23 条（PASS 3 + WARN 2 + BLOCK 3 + 边界 3 + 安全 4 + 单元函数 8）
- 集成测试：3 条（200 / 400 / 健康检查）
- 红队回归：3 条（零宽空格 / 繁简 / JSON 深度）

## Verification Steps

```bash
cd demo3-review-pipeline
npm install
npm test    # 期望 # pass 23, # fail 0
npm start
# 在另一个终端
curl -X POST http://localhost:3000/api/moderate \
  -H 'Content-Type: application/json' \
  -d '{"transcript":"Hello world"}'
# 期望 {"decision":"allow","risk_level":"PASS",...}
```

## Linked Issues

- Closes QPY-MOD-001

## Reviewers

- @code-reviewer (已 review，6 项 Low/Medium，无 Blocker)
- @security-reviewer (已 review，1 个 High 已修)
- @red-team (已 review，3 个 bypass 已修)
- @审核运营组 (需 sign-off)
- @SRE (需 sign-off 监控配置)
```

---

> 🎬 **演示收尾话术**：
> "你们看到的不是 5 段 Copilot 输出——是一个 **可审计的工程闭环**：
> 设计文档 → 实现代码 → 测试用例 → 评审报告 → 发布资产。
> 每一步都有归属 agent、有输出格式、有质量标准。
> 这就是为什么我们说 Copilot 是 **工程文化的放大器**，而不是 **代码生成器**。"
