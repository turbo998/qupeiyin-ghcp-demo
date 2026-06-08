const test = require('node:test');
const assert = require('node:assert/strict');

const { buildApp } = require('../src/app');

function startServer() {
  return new Promise((resolve) => {
    const server = buildApp().listen(0, () => {
      resolve(server);
    });
  });
}

function stopServer(server) {
  return new Promise((resolve, reject) => {
    server.close((err) => {
      if (err) {
        reject(err);
        return;
      }
      resolve();
    });
  });
}

test('GET / returns demo homepage html', async () => {
  const server = await startServer();
  const { port } = server.address();

  try {
    const res = await fetch(`http://127.0.0.1:${port}/`);
    const body = await res.text();

    assert.equal(res.status, 200);
    assert.match(res.headers.get('content-type') || '', /text\/html/);
    assert.match(body, /Demo 3 · 审核服务演示台/);
    assert.match(body, /POST \/api\/moderate/);
  } finally {
    await stopServer(server);
  }
});

test('GET /health returns service metadata', async () => {
  const server = await startServer();
  const { port } = server.address();

  try {
    const res = await fetch(`http://127.0.0.1:${port}/health`);
    const body = await res.json();

    assert.equal(res.status, 200);
    assert.equal(body.status, 'ok');
    assert.equal(body.service, 'qupeiyin-moderation');
  } finally {
    await stopServer(server);
  }
});
