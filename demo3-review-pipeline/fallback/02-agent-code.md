# Fallback 02 · Copilot Agent 模式生成代码（预跑版）

> 这是 **Step 2** 的兜底素材：现场如果 Agent 模式卡住，打开本文件展示等效代码。
> 实际仓库里 `src/moderation.js` 已经包含这套实现，可以直接对照打开。

---

## Agent Mode 工作日志（节选）

```
[1/6] Reading .github/copilot-instructions.md ............... ✓
[2/6] Reading src/moderation.js (existing skeleton) ......... ✓
[3/6] Reading src/lexicon.js ................................ ✓
[4/6] Editing src/moderation.js (add validateInput,
       detectProfanity, detectDialectMix, decide, moderate) .. ✓
[5/6] Editing tests/moderation.test.js (add PASS/WARN/BLOCK
       equivalence-class cases) ............................. ✓
[6/6] Running: npm test ..................................... ✓ pass 9
```

---

## 生成的 `src/moderation.js`（核心摘录）

```javascript
const { PROFANITY_LEXICON, DIALECT_KEYWORDS } = require('./lexicon');

class ValidationError extends Error { /* ... */ }

// 业务阈值 — 避免 magic number
const MAX_TRANSCRIPT_LENGTH = 4000;
const DIALECT_WARN_THRESHOLD = 0.05;
const DIALECT_BLOCK_THRESHOLD = 0.15;
const PROFANITY_WARN_HITS = 1;
const PROFANITY_BLOCK_HITS = 3;

const RISK_LEVELS = Object.freeze({
  PASS: 'PASS',
  WARN: 'WARN',
  BLOCK: 'BLOCK'
});

/**
 * 校验输入参数。
 * @param {unknown} transcript
 * @param {unknown} audio_meta
 * @throws {ValidationError}
 */
function validateInput(transcript, audio_meta) { /* ... */ }

/**
 * 检测低俗词命中次数（不回显具体词）。
 * @param {string} transcript
 * @returns {{ hits: number, categories: string[] }}
 */
function detectProfanity(transcript) {
  const lower = transcript.toLowerCase();
  let hits = 0;
  for (const word of PROFANITY_LEXICON) {
    if (lower.includes(word.toLowerCase())) hits += 1;
  }
  return { hits, categories: hits > 0 ? ['lexicon-hit'] : [] };
}

/**
 * 综合 profanity + dialect 给出三档决策。
 */
function decide(profanity, dialect) {
  const reasons = [];
  let level = RISK_LEVELS.PASS;

  if (profanity.hits >= PROFANITY_BLOCK_HITS) {
    level = RISK_LEVELS.BLOCK;
    reasons.push(`低俗词命中 ${profanity.hits} 次，达到 BLOCK 阈值`);
  } else if (profanity.hits >= PROFANITY_WARN_HITS) {
    level = RISK_LEVELS.WARN;
    reasons.push(`低俗词命中 ${profanity.hits} 次，建议人工复核`);
  }

  if (dialect.ratio >= DIALECT_BLOCK_THRESHOLD) {
    level = RISK_LEVELS.BLOCK;
    reasons.push(`方言 (${dialect.top_dialect}) 混入比例 ${(dialect.ratio * 100).toFixed(1)}%，超出英语配音可接受范围`);
  } else if (dialect.ratio >= DIALECT_WARN_THRESHOLD && level === RISK_LEVELS.PASS) {
    level = RISK_LEVELS.WARN;
    reasons.push(`方言 (${dialect.top_dialect}) 混入比例 ${(dialect.ratio * 100).toFixed(1)}%，建议人工复核`);
  }

  if (reasons.length === 0) {
    reasons.push('未命中低俗词，未检测到方言混入');
  }

  return { risk_level: level, reasons };
}

function moderate(transcript, audio_meta = {}) {
  validateInput(transcript, audio_meta);
  const profanity = detectProfanity(transcript);
  const dialect = detectDialectMix(transcript);
  const { risk_level, reasons } = decide(profanity, dialect);

  return {
    decision: risk_level === RISK_LEVELS.PASS ? 'allow'
            : risk_level === RISK_LEVELS.WARN ? 'review'
            : 'reject',
    risk_level,
    reasons,
    evidence: {
      profanity_hits: profanity.hits,
      profanity_categories: profanity.categories,
      dialect_ratio: Number(dialect.ratio.toFixed(4)),
      top_dialect: dialect.top_dialect,
      audio_meta_passthrough: audio_meta
    }
  };
}

module.exports = {
  ValidationError, RISK_LEVELS, MAX_TRANSCRIPT_LENGTH,
  moderate, detectProfanity, detectDialectMix, decide
};
```

---

## Agent 自己写的提交说明（候选）

```
feat: implement /api/moderate three-tier risk decision

- validateInput: empty / >4000 / non-string → ValidationError
- detectProfanity: case-insensitive substring match against
  PROFANITY_LEXICON, returns hit count + category
- detectDialectMix: keyword hit ratio against DIALECT_KEYWORDS,
  picks top dialect; capped at 1.0
- decide: WARN at 1 profanity hit OR 5% dialect ratio,
  BLOCK at 3 hits OR 15%; reasons in Chinese for ops review
- moderate: orchestrates the pipeline; evidence passes through
  audio_meta but never echoes raw lexicon words

Tests: 9 unit cases covering PASS/WARN/BLOCK + validation +
security (response does not leak raw lexicon entries).

Per copilot-instructions.md:
- No new npm deps added
- All functions < 30 lines with JSDoc
- ValidationError handled by Express middleware → 400
```

---

## Agent 自动跑测试输出

```
$ npm test

> qupeiyin-moderation-service@0.1.0 test
> node --test

TAP version 13
# Subtest: smoke: 模块可被加载且 moderate 是函数
ok 1 - smoke: 模块可被加载且 moderate 是函数
# Subtest: 干净 transcript → PASS
ok 2 - 干净 transcript → PASS
# Subtest: 含 1 个低俗词 → WARN
ok 3 - 含 1 个低俗词 → WARN
# Subtest: 含 3+ 低俗词 → BLOCK
ok 4 - 含 3+ 低俗词 → BLOCK
# Subtest: audio_meta 透传到 evidence
ok 5 - audio_meta 透传到 evidence
# Subtest: 空 transcript → ValidationError
ok 6 - 空 transcript → ValidationError
# Subtest: 超长 transcript → ValidationError
ok 7 - 超长 transcript → ValidationError
# Subtest: 非字符串 transcript → ValidationError
ok 8 - 非字符串 transcript → ValidationError
# Subtest: 响应不回显具体低俗词词条
ok 9 - 响应不回显具体低俗词词条
1..9
# tests 9
# pass 9
# fail 0
# duration_ms 74.713
```

---

## Agent 主动提示

> 我注意到 `.github/copilot-instructions.md` 要求 "新增 API endpoint 必须配套单测"。
> 当前已为 `POST /api/moderate` 添加了 9 条单测，覆盖：
> - 3 档决策（PASS / WARN / BLOCK）
> - 3 条校验边界（空 / 超长 / 非字符串）
> - 1 条 audio_meta 透传
> - 1 条安全性（响应不泄漏词库）
> - 1 条 smoke 加载
>
> **不在本次实现范围（建议下个 PR）**：
> - 方言识别的 Unicode 同形字归一化（`@red-team` 会在 Step 4 复现）
> - 词库热加载（`@architect` 已列入 Open Questions）
>
> 是否继续？还是先让 `@test-engineer` 把等价类补全？
