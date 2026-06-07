/**
 * 趣配音 · 内容审核服务 — 核心审核逻辑.
 *
 * 输入：transcript (string) + audio_meta (object)
 * 输出：决策对象 { decision, risk_level, reasons, evidence }
 *
 * 注意：这是 demo 骨架，所有检测都是 mock。
 *      现场会让 Copilot Agent (@architect / @code-reviewer / @red-team)
 *      把检测细化为真实实现，并补全 PASS / WARN / BLOCK 等价类测试。
 */

const { PROFANITY_LEXICON, DIALECT_KEYWORDS } = require('./lexicon');

class ValidationError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ValidationError';
  }
}

// 业务阈值 — 避免 magic number
const MAX_TRANSCRIPT_LENGTH = 4000;
const DIALECT_WARN_THRESHOLD = 0.05; // 方言词占比 >= 5% → WARN
const DIALECT_BLOCK_THRESHOLD = 0.15; // >= 15% → BLOCK
const PROFANITY_WARN_HITS = 1;        // ≥1 命中 → WARN
const PROFANITY_BLOCK_HITS = 3;       // ≥3 命中 → BLOCK

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
function validateInput(transcript, audio_meta) {
  if (typeof transcript !== 'string' || transcript.trim().length === 0) {
    throw new ValidationError('transcript 不能为空，请传入 1-4000 字符的字符串');
  }
  if (transcript.length > MAX_TRANSCRIPT_LENGTH) {
    throw new ValidationError(
      `transcript 超长 (>${MAX_TRANSCRIPT_LENGTH} 字符)，请分片后重试`
    );
  }
  if (audio_meta !== undefined && (typeof audio_meta !== 'object' || audio_meta === null)) {
    throw new ValidationError('audio_meta 必须是对象或缺省');
  }
}

/**
 * 检测低俗词命中次数（不回显具体词）。
 * @param {string} transcript
 * @returns {{ hits: number, categories: string[] }}
 */
function detectProfanity(transcript) {
  const lower = transcript.toLowerCase();
  let hits = 0;
  for (const word of PROFANITY_LEXICON) {
    if (lower.includes(word.toLowerCase())) {
      hits += 1;
    }
  }
  // 真实实现会按词分类（侮辱 / 性 / 暴力 等）。demo 仅给总数。
  return { hits, categories: hits > 0 ? ['lexicon-hit'] : [] };
}

/**
 * 检测方言混入比例。
 * 简化算法：(命中方言关键词数) / max(transcript 长度按 2 字 chunk, 1)
 * @param {string} transcript
 * @returns {{ ratio: number, top_dialect: string|null }}
 */
function detectDialectMix(transcript) {
  let topDialect = null;
  let topHits = 0;
  for (const [dialect, keywords] of Object.entries(DIALECT_KEYWORDS)) {
    const hits = keywords.reduce(
      (acc, kw) => acc + (transcript.includes(kw) ? 1 : 0),
      0
    );
    if (hits > topHits) {
      topHits = hits;
      topDialect = dialect;
    }
  }
  // 粗糙比例：命中次数 / (transcript 长度/2)，封顶 1.0
  const denom = Math.max(transcript.length / 2, 1);
  const ratio = Math.min(topHits / denom, 1);
  return { ratio, top_dialect: topHits > 0 ? topDialect : null };
}

/**
 * 综合 profanity + dialect 给出三档决策。
 * @param {{hits:number}} profanity
 * @param {{ratio:number, top_dialect:string|null}} dialect
 * @returns {{ risk_level: string, reasons: string[] }}
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
    reasons.push(
      `方言 (${dialect.top_dialect}) 混入比例 ${(dialect.ratio * 100).toFixed(1)}%，超出英语配音可接受范围`
    );
  } else if (dialect.ratio >= DIALECT_WARN_THRESHOLD && level === RISK_LEVELS.PASS) {
    level = RISK_LEVELS.WARN;
    reasons.push(
      `方言 (${dialect.top_dialect}) 混入比例 ${(dialect.ratio * 100).toFixed(1)}%，建议人工复核`
    );
  }

  if (reasons.length === 0) {
    reasons.push('未命中低俗词，未检测到方言混入');
  }

  return { risk_level: level, reasons };
}

/**
 * 主入口：对一段 transcript + audio_meta 做内容审核。
 * @param {string} transcript - 学生配音 ASR 文本
 * @param {object} [audio_meta] - 音频元数据（duration_sec / sample_rate 等）
 * @returns {{decision:string, risk_level:string, reasons:string[], evidence:object}}
 * @throws {ValidationError}
 */
function moderate(transcript, audio_meta = {}) {
  validateInput(transcript, audio_meta);

  const profanity = detectProfanity(transcript);
  const dialect = detectDialectMix(transcript);
  const { risk_level, reasons } = decide(profanity, dialect);

  return {
    decision: risk_level === RISK_LEVELS.PASS ? 'allow' : risk_level === RISK_LEVELS.WARN ? 'review' : 'reject',
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
  ValidationError,
  RISK_LEVELS,
  MAX_TRANSCRIPT_LENGTH,
  moderate,
  // 暴露给测试 & Copilot 扩展
  detectProfanity,
  detectDialectMix,
  decide
};
