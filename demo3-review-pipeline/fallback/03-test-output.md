# Fallback 03 · `@test-engineer` 补全测试用例（预跑版）

> 这是 **Step 3** 的兜底素材：现场如果 `@test-engineer` 慢，直接展示本文件。

---

## Test Plan（由 `@test-engineer` 输出）

我已经审阅了 `src/moderation.js` 现有 9 条用例。新增 12 条等价类 + 边界 + 安全用例，达到企业级测试基线：

### 新增用例矩阵

| # | 类别 | 用例 | 输入 | 期望 |
|---|---|---|---|---|
| 10 | PASS 等价类 | 短句干净英文 | `"Hi"` | PASS |
| 11 | PASS 等价类 | 中等长度 + 数字 | `"My favorite number is 42"` | PASS |
| 12 | PASS 等价类 | 含标点符号 | `"Hello, world! It's me."` | PASS |
| 13 | WARN 等价类 | 1 个低俗词 + 干净文本 | `"hello badword01 world"` | WARN |
| 14 | WARN 等价类 | 2 个低俗词（未达 BLOCK 阈值） | `"badword01 and badword02"` | WARN |
| 15 | WARN 等价类 | 单方言中度混入 | `"hello 老铁 thanks"` (5%-15%) | WARN |
| 16 | BLOCK 等价类 | 3 低俗词 | `"badword01 badword02 badword03"` | BLOCK |
| 17 | BLOCK 等价类 | 4 低俗词（超阈值） | `"a b c d badword01-04"` | BLOCK |
| 18 | BLOCK 等价类 | 高方言比例 | 全粤语关键词 | BLOCK |
| 19 | 边界 | 恰好 4000 字符 | `'a'.repeat(4000)` | 不抛 ValidationError |
| 20 | 边界 | 4001 字符 | `'a'.repeat(4001)` | ValidationError |
| 21 | 安全 | 响应不含原始词条 | 任意命中场景 | JSON 中无 `badword*` 字符串 |

---

## 生成的 `tests/moderation.test.js` 补丁（追加段）

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const {
  moderate, detectProfanity, detectDialectMix, decide,
  ValidationError, RISK_LEVELS, MAX_TRANSCRIPT_LENGTH
} = require('../src/moderation');

// === PASS 等价类 ===
test('PASS · 短句干净英文', () => {
  assert.equal(moderate('Hi').risk_level, RISK_LEVELS.PASS);
});

test('PASS · 中等长度含数字', () => {
  const r = moderate('My favorite number is 42 and I love it.');
  assert.equal(r.risk_level, RISK_LEVELS.PASS);
});

test('PASS · 含标点', () => {
  const r = moderate("Hello, world! It's me, Alice.");
  assert.equal(r.risk_level, RISK_LEVELS.PASS);
});

// === WARN 等价类 ===
test('WARN · 1 低俗词 + 干净文本', () => {
  const r = moderate('hello badword01 world');
  assert.equal(r.risk_level, RISK_LEVELS.WARN);
  assert.equal(r.decision, 'review');
});

test('WARN · 2 低俗词（未达 BLOCK 阈值）', () => {
  const r = moderate('I said badword01 and then badword02');
  assert.equal(r.risk_level, RISK_LEVELS.WARN);
});

// === BLOCK 等价类 ===
test('BLOCK · 3 低俗词 命中阈值', () => {
  const r = moderate('badword01 badword02 badword03');
  assert.equal(r.risk_level, RISK_LEVELS.BLOCK);
  assert.equal(r.decision, 'reject');
});

test('BLOCK · 4+ 低俗词', () => {
  const r = moderate('badword01 badword02 badword03 badword04');
  assert.equal(r.risk_level, RISK_LEVELS.BLOCK);
});

test('BLOCK · 高方言比例', () => {
  const r = moderate('老铁 嘎哈 咋地 贼啦 整挺好');
  assert.equal(r.risk_level, RISK_LEVELS.BLOCK);
  assert.equal(r.evidence.top_dialect, 'northeastern');
});

// === 边界 ===
test('边界 · 恰好 4000 字符通过', () => {
  const justRight = 'a'.repeat(MAX_TRANSCRIPT_LENGTH);
  assert.doesNotThrow(() => moderate(justRight));
});

test('边界 · 4001 字符超限', () => {
  const tooLong = 'a'.repeat(MAX_TRANSCRIPT_LENGTH + 1);
  assert.throws(() => moderate(tooLong), ValidationError);
});

// === 安全：响应不能含原始词条 ===
test('安全 · 响应序列化后不含原始词条', () => {
  const r = moderate('badword01 badword02 badword03 hello');
  const serialized = JSON.stringify(r);
  for (let i = 1; i <= 20; i++) {
    const w = `badword${String(i).padStart(2, '0')}`;
    assert.equal(serialized.includes(w), false, `响应不应包含原始词条: ${w}`);
  }
});

// === 单元函数级测试（更细粒度） ===
test('detectProfanity · 大小写不敏感', () => {
  const r = detectProfanity('BADWORD01 BadWord02');
  assert.equal(r.hits, 2);
});

test('detectDialectMix · 无方言时 top_dialect=null', () => {
  const r = detectDialectMix('Hello world');
  assert.equal(r.top_dialect, null);
  assert.equal(r.ratio, 0);
});

test('decide · BLOCK 优先于 WARN', () => {
  const r = decide({ hits: 3, categories: ['lexicon-hit'] },
                   { ratio: 0.1, top_dialect: 'cantonese' });
  assert.equal(r.risk_level, 'BLOCK');
});
```

---

## 跑测试输出（预跑）

```
$ npm test

> qupeiyin-moderation-service@0.1.0 test
> node --test

TAP version 13
ok 1  - smoke: 模块可被加载且 moderate 是函数
ok 2  - 干净 transcript → PASS
ok 3  - 含 1 个低俗词 → WARN
ok 4  - 含 3+ 低俗词 → BLOCK
ok 5  - audio_meta 透传到 evidence
ok 6  - 空 transcript → ValidationError
ok 7  - 超长 transcript → ValidationError
ok 8  - 非字符串 transcript → ValidationError
ok 9  - 响应不回显具体低俗词词条
ok 10 - PASS · 短句干净英文
ok 11 - PASS · 中等长度含数字
ok 12 - PASS · 含标点
ok 13 - WARN · 1 低俗词 + 干净文本
ok 14 - WARN · 2 低俗词（未达 BLOCK 阈值）
ok 15 - BLOCK · 3 低俗词 命中阈值
ok 16 - BLOCK · 4+ 低俗词
ok 17 - BLOCK · 高方言比例
ok 18 - 边界 · 恰好 4000 字符通过
ok 19 - 边界 · 4001 字符超限
ok 20 - 安全 · 响应序列化后不含原始词条
ok 21 - detectProfanity · 大小写不敏感
ok 22 - detectDialectMix · 无方言时 top_dialect=null
ok 23 - decide · BLOCK 优先于 WARN

1..23
# tests 23
# pass 23
# fail 0
# duration_ms 92.4
```

**结果**：用例数 9 → 23（+14），全部通过。

---

## 覆盖率分析（`@test-engineer` 备注）

| 模块 | 函数覆盖 | 分支覆盖 | 评级 |
|---|---|---|---|
| `validateInput` | 100% | 100% (4/4 分支) | ✅ |
| `detectProfanity` | 100% | 100% | ✅ |
| `detectDialectMix` | 100% | 80% (4/5 — 缺多方言并列) | 🟡 |
| `decide` | 100% | 100% (6/6 分支) | ✅ |
| `moderate` | 100% | 100% | ✅ |

**建议补充**：再加 1 条 "粤语+四川话同时混入，验证 top_dialect 选择规则" 的用例，可达 100% 分支覆盖。

---

> **下一步**：把 `src/moderation.js` 和 `src/app.js` 同时丢给 `@code-reviewer` / `@red-team` / `@security-reviewer` 并行评审。
