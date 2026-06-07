# Fallback 04 · 三视角并行评审报告（预跑版）

> 这是 **Step 4** 的兜底素材：**高光时刻**的备份。
> 三个 Copilot Chat 窗口并行召唤 `@code-reviewer` + `@red-team` + `@security-reviewer`，
> 实际跑出来 30 秒拿到 3 份风格完全不同的评审。

---

# 📝 Report A · `@code-reviewer` 代码评审

**评审范围**: `src/moderation.js`, `src/app.js`
**评审耗时**: 22 秒
**总体结论**: 🟢 **Approve with minor suggestions**

## Findings Table

| # | 严重度 | 类别 | 文件 | 行 | 发现 | 建议 |
|---|---|---|---|---|---|---|
| 1 | 🟡 Medium | 可读性 | `moderation.js` | 137-143 | `moderate` 函数末尾三元嵌套 `risk_level === PASS ? 'allow' : risk_level === WARN ? 'review' : 'reject'` 不易读 | 提取 `RISK_TO_DECISION` 常量映射表 |
| 2 | 🟡 Medium | DRY | `moderation.js` | 95-115 | `decide` 函数里 BLOCK / WARN 的 reasons 字符串模板重复 | 抽取 `formatProfanityReason(hits, level)` |
| 3 | 🔵 Low | 命名 | `moderation.js` | 78 | `denom` 命名太缩写 | 改为 `denominator` 或 `tokenCount` |
| 4 | 🔵 Low | 注释 | `lexicon.js` | 全文 | `PROFANITY_LEXICON` 注释提到 200 条但实际 20 条 placeholder | 注释加上 "demo 用 20 条 placeholder，生产为 200+" |
| 5 | 🔵 Low | JSDoc | `app.js` | 6 | `buildApp` 缺少 `@example` 段 | 补 1 个最小调用示例 |
| 6 | 🔵 Low | 错误信息 | `moderation.js` | 49 | `audio_meta 必须是对象或缺省` 错误信息可以更 actionable | 给出正确格式示例：`如 {duration_sec: 8.5}` |

## Summary
- **Total findings**: 6
- **Blockers**: 0
- **建议**: ✅ **Approve**，6 项均可在 follow-up PR 处理，不阻塞当前功能上线。

## 亮点（值得保留）
- ✅ 函数职责单一，每个函数 < 30 行符合规范
- ✅ 阈值全部常量化，没有 magic number
- ✅ 响应安全设计到位（不回显原始词条）
- ✅ JSDoc 覆盖所有 exported 函数
- ✅ `Object.freeze(RISK_LEVELS)` 防止运行时被改写

---

# 🔴 Report B · `@red-team` 红队对抗

**攻击范围**: `POST /api/moderate`
**攻击耗时**: 28 秒
**总体结论**: ⚠️ **3 个可利用 bypass，建议修复后再上线**

## 攻击 PoC 表格

| # | 严重度 | 攻击向量 | PoC payload | 当前行为 | 期望行为 | Fix 建议 |
|---|---|---|---|---|---|---|
| 1 | 🔴 Critical | **零宽空格 bypass** | `"bad\u200Bword01 bad\u200Bword02 bad\u200Bword03"` | PASS（命中 0 条） | BLOCK | 在 `validateInput` 后加 `transcript = transcript.replace(/[\u200B-\u200D\uFEFF]/g, '')` 归一化 |
| 2 | 🟠 High | **Unicode 同形字（粤语字繁简变体）** | `"巴適 巴適 巴適"` (繁体"適" vs lexicon "适") | PASS | BLOCK / WARN | 加入 `transcript.normalize('NFKC')` 并扩展词库变体 |
| 3 | 🟠 High | **JSON 嵌套滥用** | `{"transcript":"hi","audio_meta":{"a":{"b":{...深 1000 层}}}}` | 接收并 passthrough 到响应 evidence | 拒绝或截断 | 限制 audio_meta JSON 深度 ≤ 3 层 |
| 4 | 🟡 Medium | **大小写 + 全角变体** | `"ＢＡＤＷＯＲＤ０１"` (全角字符) | PASS | BLOCK | normalize NFKC 后再 toLowerCase |
| 5 | 🟡 Medium | **方言关键词稀释** | `"a".repeat(3000) + "巴适"` | PASS (ratio 0.0003%) | 仍 PASS（设计如此） | 这是设计行为，但建议告警：transcript 过长 + 含方言关键词时打 audit 日志 |
| 6 | 🟡 Medium | **HTTP 方法滥用** | `GET /api/moderate?transcript=...` | 404（Express 默认） | 405 Method Not Allowed | 显式处理 405 + Allow header |
| 7 | 🔵 Low | **Content-Type 缺失** | `POST` 不带 `Content-Type` | `req.body = undefined` → 400 | 当前行为 OK | 无需改 |
| 8 | 🔵 Low | **超大 body** | 256kb+1 字节 body | Express 自动 413 | 当前行为 OK | 无需改 |

## 攻击复盘

🔴 **#1 零宽空格** 是最关键的漏洞。学生只要在审核服务上下文里学会插入 `\u200B`，
词库就形同虚设。这是真实场景中已知被滥用的技巧（参见 OWASP A04:2021）。

🟠 **#2 Unicode 变体** 在 K12 场景被低估——学生用输入法切繁体字就能绕过。

## Recommendation

⛔ **Request Changes**：#1 必须修，#2 #3 强烈建议修。

修复后建议追加 3 条红队回归测试：
```javascript
test('安全 · 零宽空格 bypass 应被识别', () => {
  const r = moderate('bad\u200Bword01 bad\u200Bword02 bad\u200Bword03');
  assert.equal(r.risk_level, 'BLOCK');
});
test('安全 · 繁体字方言变体应被识别', () => {
  const r = moderate('巴適'.repeat(10));
  assert.notEqual(r.risk_level, 'PASS');
});
test('安全 · audio_meta 深嵌套应被拒绝', () => {
  let nested = {};
  let cur = nested;
  for (let i = 0; i < 1000; i++) { cur.a = {}; cur = cur.a; }
  // 期望 400 或截断
});
```

---

# 🔒 Report C · `@security-reviewer` 安全评审

**评审范围**: `src/moderation.js`, `src/app.js`, `src/lexicon.js`
**评审耗时**: 25 秒
**总体结论**: 🟡 **Conditional Approve — 修复 1 项 High 后放行**

## Findings Table

| # | Severity | Category | File | Line | Finding | Recommendation |
|---|---|---|---|---|---|---|
| 1 | 🟠 High | Input Validation | `moderation.js` | 38-52 | `validateInput` 未做 Unicode normalize / 控制字符 strip，与 @red-team 发现的零宽空格 bypass 是同一根因 | 加 `transcript = transcript.normalize('NFKC').replace(/[\u0000-\u001F\u200B-\u200D]/g,'')` |
| 2 | 🟡 Medium | DoS / ReDoS | `moderation.js` | 60-65 | `detectProfanity` 用 `String.includes` 是 O(n*m)，词库 200 条 × transcript 4000 字 = 800k 次比较，最坏 case 每请求 ~3ms。当前安全，但词库扩到 2000 条需复测 | 词库 >500 时改用 Aho-Corasick 或 trie；现阶段加单测：4000 字 transcript P95 ≤ 50ms |
| 3 | 🟡 Medium | Logging | `app.js` | 36 | `console.warn` 记录 `err.message` 时，若上游传入恶意构造的 transcript 作为错误信息（理论上不会，但兜底） | logger 加 sanitize：长度截断 ≤ 200 + 转义 |
| 4 | 🔵 Low | Stack Trace | `app.js` | 35-37 | 500 兜底响应正确，未泄漏 stack ✅ | 无需改 |
| 5 | 🔵 Low | Lexicon Exposure | `moderation.js` | 64 | `detectProfanity` 返回 `categories: ['lexicon-hit']` 是抽象分类，未泄漏具体词条 ✅ | 无需改 |
| 6 | 🔵 Low | CORS | `app.js` | — | 未配置 CORS，默认拒所有跨域 | 上线前由网关层统一处理 |
| 7 | 🔵 Low | Rate Limit | `app.js` | — | 无应用层频次限制 | 由 API 网关 / WAF 处理，应用层不重复实现 |
| 8 | 🔵 Low | Secret Mgmt | `lexicon.js` | — | 当前词库写死在代码，正式版应来自加密配置 | `@architect` 在 Open Questions 已列入下期 |

## Summary
- **Total findings**: 8 (1 High, 2 Medium, 5 Low)
- **Blockers**: 1（#1 Unicode 归一化）
- **Recommendation**: ⚠️ **Request Changes** — 修 #1 后可放行

## 合规观察
- ✅ 未成年人内容场景下，"宁可误报为 WARN"的设计原则已体现在 `decide` 函数（OR 逻辑取严）
- ✅ 词库不在响应回显，符合《未成年人保护法》对敏感词管理的隐性要求
- ⚠️ 建议加 audit log：所有 BLOCK 决策落库，保留 6 个月（合规审计要求）

---

# 🔀 三视角合并 — 统一行动项

| 优先级 | 来源 | 行动项 | 工作量 | 负责人 |
|---|---|---|---|---|
| **P0** | red-team #1 + security #1 | 加 Unicode normalize + 零宽空格 strip | 0.5h | 工程师 A |
| **P0** | red-team #2 | 词库扩展繁体变体 | 1h | 审核运营 |
| **P1** | red-team #3 | 限制 audio_meta JSON 深度 | 0.5h | 工程师 A |
| **P1** | security #2 | 加 P95 延迟测试 | 1h | `@test-engineer` |
| **P2** | code-reviewer #1-2 | 抽取常量映射 / 工具函数 | 1h | 工程师 A |
| **P2** | security #3 | logger sanitize | 0.5h | 工程师 A |
| **P3** | code-reviewer #3-6 | 命名 + 注释 + JSDoc 补充 | 0.5h | 工程师 A |

**总工作量**: ~5 小时。修完 P0 + P1 即可放行 release。

---

> **下一步**：把上述 P0/P1 修复合入后，调用 `@release-engineer` 出 CHANGELOG 和 release notes。
