# Fallback 01 · `@architect` 技术设计输出（预跑版）

> 这是 **Step 1** 的兜底素材：现场如果 Copilot Chat 慢或挂掉，直接打开本文件演示。
> 内容是 FDE 提前用同一条 `/design-feature` prompt 跑出来的真实输出（已轻度排版）。

---

## Architecture Overview

```
┌─────────────────┐     POST /api/moderate     ┌───────────────────────────────┐
│  上游调用方     │ ─────────────────────────▶ │   Moderation Service (Node)   │
│  - 配音上传链路 │   { transcript,             │  ┌─────────────────────────┐  │
│  - 教师批阅链路 │     audio_meta }            │  │  validateInput          │  │
│  - 素材入库链路 │                              │  └──────────┬──────────────┘  │
└─────────────────┘                              │             ▼                  │
                                                 │  ┌─────────────────────────┐  │
                                                 │  │  detectProfanity        │──┼──▶ lexicon.js (200 词)
                                                 │  └──────────┬──────────────┘  │
                                                 │             ▼                  │
                                                 │  ┌─────────────────────────┐  │
                                                 │  │  detectDialectMix       │──┼──▶ DIALECT_KEYWORDS
                                                 │  └──────────┬──────────────┘  │
                                                 │             ▼                  │
                                                 │  ┌─────────────────────────┐  │
                                                 │  │  decide(profanity,      │  │
                                                 │  │         dialect)        │  │
                                                 │  └──────────┬──────────────┘  │
                                                 └─────────────┼──────────────────┘
                                                               │
                                       { decision, risk_level, │
                                         reasons, evidence }   ▼
                                                ┌───────────────────────────────┐
                                                │   下游消费方                  │
                                                │   - 审核工作台 (WARN 人审)    │
                                                │   - 自动拦截器 (BLOCK)         │
                                                │   - 数据看板 (全量埋点)        │
                                                └───────────────────────────────┘
```

**关键边界**：
- 词库加载在进程启动时一次性完成，**不放到请求路径**
- detectProfanity / detectDialectMix 是 **纯函数**，可独立测试
- 响应 evidence 只给计数和分类，**不回显原始词条**

---

## Data Flow

1. 上游 POST 到 `/api/moderate`，Express 中间件 parse JSON（限制 256kb）
2. `validateInput` 校验：transcript 是 string、长度 1-4000、audio_meta 是 object 或缺省
3. `detectProfanity(transcript)` → `{ hits, categories }`
4. `detectDialectMix(transcript)` → `{ ratio, top_dialect }`
5. `decide(profanity, dialect)` → `{ risk_level, reasons[] }`
6. 组装响应：`{ decision, risk_level, reasons, evidence }`，evidence 透传 audio_meta
7. 异常路径：`ValidationError` → 400；其它 → 500 兜底（不回显 stack）

---

## API Design

| Method | Path | Request Body | Success Response | Error Responses |
|--------|------|--------------|------------------|-----------------|
| GET    | `/health` | — | `200 {status:"ok",service,version}` | — |
| POST   | `/api/moderate` | `{transcript:string, audio_meta?:object}` | `200 {decision,risk_level,reasons,evidence}` | `400 {error}` 校验失败 / `500 {error}` 兜底 |

**risk_level 取值**：`PASS` / `WARN` / `BLOCK`
**decision 取值**：`allow` / `review` / `reject`

---

## Edge Cases

1. **空 transcript** → 400 "transcript 不能为空"
2. **transcript 只有空白字符** → 400（同上）
3. **transcript = 4000 字符** → 通过校验
4. **transcript = 4001 字符** → 400 "transcript 超长"
5. **transcript 全是低俗词** → BLOCK + reasons 解释
6. **transcript 全是粤语关键词** → BLOCK（dialect ratio 接近 1）
7. **transcript 含 Unicode 同形字（粤语"係" vs 普通话"系"）** → 当前 mock 不识别，列为已知 gap，红队会再攻一次
8. **transcript 含零宽空格 `\u200B` 插入到 badword01 中间** → 当前实现 bypass，需要规范化（加 normalize 步骤）
9. **audio_meta = null** → 当作缺省处理，evidence 里 passthrough 为 `{}`
10. **audio_meta 是字符串** → 400 "audio_meta 必须是对象或缺省"
11. **同时命中低俗词 + 方言** → 取**更严**的 level（BLOCK 优先 WARN）
12. **重复请求幂等性** → 当前函数纯，幂等无问题
13. **并发请求** → 词库是 const，无竞态

---

## Test Strategy Matrix

| Feature | Unit | Integration | E2E | 优先级 |
|---|---|---|---|---|
| validateInput 边界 | ✅ 必须 | — | — | P0 |
| detectProfanity 计数准确 | ✅ 必须 | — | — | P0 |
| detectDialectMix 比例计算 | ✅ 必须 | — | — | P0 |
| decide 三档决策矩阵 | ✅ 必须 | — | — | P0 |
| POST /api/moderate 200 路径 | — | ✅ 必须 | — | P0 |
| POST /api/moderate 400 路径 | — | ✅ 必须 | — | P0 |
| 响应不回显原始词条 | ✅ 必须 | ✅ 必须 | — | P0 (安全) |
| 同形字 / 零宽空格 bypass | ✅ 应有 | — | ✅ 可选 | P1 (红队对抗) |
| 4000 字 P95 延迟 ≤ 50ms | — | — | ✅ 应有 | P1 (性能) |
| 词库热更新 | — | ✅ 下期 | — | P2 (下迭代) |

---

## Recommendations

1. **必做（本期）**
   - 在 `validateInput` 之后增加一个 `normalizeTranscript` 步骤：strip 零宽空格、统一大小写、NFC unicode normalize。这能挡住 80% 的简单 bypass。
   - 词库支持从环境变量 `LEXICON_PATH` 指向外部 JSON 加载，但保留内置 fallback。
   - 错误响应统一中间件，禁止 stack 泄漏。

2. **建议（下期）**
   - 方言识别从关键词命中升级为 **声学模型 + ASR 双信号**。当前 API 契约可平滑替换。
   - 词库支持热加载（SIGHUP 或 PubSub），运营后台直接生效。
   - 加 `request_id` 透传，便于审核工作台回溯。

3. **架构权衡**
   - **不引入 LLM 做兜底审核**：延迟不可控（>500ms），且词库可解释性是合规要求。LLM 只在 WARN 档作为人工辅助。
   - **不做缓存**：transcript 重复率低（学生每次录音不同），缓存命中率 <1%，不划算。

---

## Open Questions

- [ ] 词库的多分类（侮辱 / 性 / 暴力 / 政治）是否在本期划分？运营组需要明确分类粒度。
- [ ] BLOCK 之后是否需要发回调通知上游？还是上游轮询？
- [ ] 是否对学生 ID 做频次限制（同一学生 1 小时内 3 次 BLOCK 触发账号冻结）？

---

> **下一步**：把这份设计转给 `@code-reviewer` 复核数据流，
> 然后切到 Copilot Agent 模式开始实现 `src/moderation.js`。
