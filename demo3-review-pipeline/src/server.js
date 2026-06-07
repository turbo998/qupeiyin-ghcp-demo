const { buildApp } = require('./app');

const port = Number(process.env.PORT ?? 3000);
const app = buildApp();

app.listen(port, () => {
  console.log(`[moderation] 趣配音内容审核服务监听在 http://localhost:${port}`);
  console.log(`[moderation]   GET  /health`);
  console.log(`[moderation]   POST /api/moderate   body={ transcript, audio_meta }`);
});
