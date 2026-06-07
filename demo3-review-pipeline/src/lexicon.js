/**
 * 趣配音 · 内容审核服务 — 初始词库 (mock).
 *
 * ⚠️ 真实生产环境的词库来自独立的配置仓 / 审核运营后台，
 *    这里仅作为 demo 占位。词库内容**不得**出现在响应体或日志原文。
 *
 * 词库规模：本 demo 提供 ~20 条 placeholder（生产为 200+）。
 * 真实词库由审核运营维护，FDE 现场会演示如何用 @architect
 * 设计「词库热加载 + 灰度」方案。
 */

/**
 * 低俗词词库（示意 placeholder，不是真实敏感词）。
 * 真实场景下会被替换为加密的外部 JSON。
 * @type {string[]}
 */
const PROFANITY_LEXICON = [
  // 仅为演示结构，不是真实敏感词
  'badword01', 'badword02', 'badword03', 'badword04', 'badword05',
  'badword06', 'badword07', 'badword08', 'badword09', 'badword10',
  'badword11', 'badword12', 'badword13', 'badword14', 'badword15',
  'badword16', 'badword17', 'badword18', 'badword19', 'badword20'
];

/**
 * 方言关键词命中表（mock）。
 * key  = 方言 code
 * vals = 该方言的标志性词汇 / 助词 / 语气词
 * 真实生产会用声学模型 + 方言分类器替换。
 * @type {Record<string, string[]>}
 */
const DIALECT_KEYWORDS = {
  cantonese: ['冇', '係', '唔該', '嘅', '咩', '嚟'],         // 粤语
  sichuanese: ['巴适', '安逸', '搞快点', '要得', '撒子'],     // 四川话
  northeastern: ['老铁', '嘎哈', '咋地', '贼啦', '整挺好']    // 东北话
};

module.exports = {
  PROFANITY_LEXICON,
  DIALECT_KEYWORDS
};
