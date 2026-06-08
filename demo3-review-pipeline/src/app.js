const path = require('node:path');
const express = require('express');
const { moderate, ValidationError } = require('./moderation');

const HOME_PAGE = path.join(__dirname, '..', 'static', 'index.html');

/**
 * 构建 Express App（导出工厂便于测试）。
 * @returns {import('express').Express}
 */
function buildApp() {
  const app = express();
  app.use(express.json({ limit: '256kb' }));

  app.get('/', (_req, res) => {
    res.sendFile(HOME_PAGE, (err) => {
      if (err) {
        res
          .status(500)
          .type('html')
          .send('<h1>Demo 3 首页缺失</h1><p>请检查 demo3-review-pipeline/static/index.html</p>');
      }
    });
  });

  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', service: 'qupeiyin-moderation', version: '0.1.0' });
  });

  /**
   * 核心审核 API.
   * POST /api/moderate
   * body: { transcript: string, audio_meta?: object }
   */
  app.post('/api/moderate', (req, res, next) => {
    try {
      const { transcript, audio_meta } = req.body ?? {};
      const result = moderate(transcript, audio_meta);
      res.status(200).json(result);
    } catch (err) {
      if (err instanceof ValidationError) {
        res.status(400).json({ error: err.message });
        return;
      }
      next(err);
    }
  });

  // 兜底 500 — 严禁回显 stack
  // eslint-disable-next-line no-unused-vars
  app.use((err, _req, res, _next) => {
    console.warn('[moderation] unhandled error:', err.message);
    res.status(500).json({ error: '内部错误，请稍后重试' });
  });

  return app;
}

module.exports = { buildApp };
