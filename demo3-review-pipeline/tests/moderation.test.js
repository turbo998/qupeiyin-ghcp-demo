const test = require('node:test');
const assert = require('node:assert/strict');

const {
  moderate,
  ValidationError,
  RISK_LEVELS,
  MAX_TRANSCRIPT_LENGTH
} = require('../src/moderation');

// ---- 占位 smoke test (任务最低要求：哪怕 1 个 pass 也行) ----
test('smoke: 模块可被加载且 moderate 是函数', () => {
  assert.equal(typeof moderate, 'function');
  assert.equal(typeof RISK_LEVELS.PASS, 'string');
});

// ---- PASS / WARN / BLOCK 三档基本用例 ----
// 这些是给 Copilot @test-engineer 在 SOP 步骤 3 扩展的种子用例
test('干净 transcript → PASS', () => {
  const result = moderate('Hello, my name is Alice. I love English.', {
    duration_sec: 4.2
  });
  assert.equal(result.risk_level, RISK_LEVELS.PASS);
  assert.equal(result.decision, 'allow');
  assert.ok(Array.isArray(result.reasons));
});

test('含 1 个低俗词 → WARN', () => {
  const result = moderate('Hello badword01 world');
  assert.equal(result.risk_level, RISK_LEVELS.WARN);
  assert.equal(result.decision, 'review');
});

test('含 3+ 低俗词 → BLOCK', () => {
  const result = moderate('badword01 badword02 badword03 some text');
  assert.equal(result.risk_level, RISK_LEVELS.BLOCK);
  assert.equal(result.decision, 'reject');
});

test('audio_meta 透传到 evidence', () => {
  const meta = { duration_sec: 8.5, sample_rate: 16000 };
  const result = moderate('Hello world', meta);
  assert.deepEqual(result.evidence.audio_meta_passthrough, meta);
});

// ---- 输入校验 ----
test('空 transcript → ValidationError', () => {
  assert.throws(() => moderate(''), ValidationError);
  assert.throws(() => moderate('   '), ValidationError);
});

test('超长 transcript → ValidationError', () => {
  const tooLong = 'a'.repeat(MAX_TRANSCRIPT_LENGTH + 1);
  assert.throws(() => moderate(tooLong), ValidationError);
});

test('非字符串 transcript → ValidationError', () => {
  assert.throws(() => moderate(null), ValidationError);
  assert.throws(() => moderate(123), ValidationError);
});

// ---- 安全：响应体里不能出现原始词库词 ----
test('响应不回显具体低俗词词条', () => {
  const result = moderate('Hello badword01 world');
  const serialized = JSON.stringify(result);
  assert.equal(
    serialized.includes('badword01'),
    false,
    '响应里不应包含原始词库词条'
  );
});
