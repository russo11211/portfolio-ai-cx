// Step 6 - a real sender: GitHub (X-Hub-Signature-256, X-GitHub-Delivery, X-GitHub-Event).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { load, post, memoryLogger, recordingHandler, SECRET } from './helpers.js';

const { createApp } = await load('app.js');

const ping = { zen: 'Keep it logically awesome.', hook_id: 123 };
const githubHeaders = (delivery = '72d3162e-cc78-11e3-81ab-4c9367dc0958', event = 'ping') => ({
  'X-GitHub-Delivery': delivery,
  'X-GitHub-Event': event,
});

function githubApp(rec) {
  return createApp({ secret: SECRET, source: 'github', logger: memoryLogger(), handleEvent: rec.handleEvent });
}

test('step 6: a GitHub ping signed in X-Hub-Signature-256 is accepted', async () => {
  const rec = recordingHandler();
  const app = githubApp(rec);
  const res = await post(app, ping, { header: 'X-Hub-Signature-256', headers: githubHeaders() });
  assert.equal(res.status, 200);
  await app.locals.queue.onIdle();
  assert.equal(rec.calls.length, 1);
});

test('step 6: the event id comes from X-GitHub-Delivery and the type from X-GitHub-Event', async () => {
  const rec = recordingHandler();
  const app = githubApp(rec);
  await post(app, { ref: 'refs/heads/main' }, { header: 'X-Hub-Signature-256', headers: githubHeaders('d-42', 'push') });
  await app.locals.queue.onIdle();
  assert.deepEqual(rec.calls[0], { id: 'd-42', type: 'github.push', data: { ref: 'refs/heads/main' } });
});

test('step 6: in GitHub mode the generic X-Signature-256 header is NOT accepted', async () => {
  const app = githubApp(recordingHandler());
  const res = await post(app, ping, { header: 'X-Signature-256', headers: githubHeaders() });
  assert.equal(res.status, 401);
});

test('step 6: a wrong GitHub signature gets 401', async () => {
  const app = githubApp(recordingHandler());
  const res = await post(app, ping, { header: 'X-Hub-Signature-256', secret: 'nope', headers: githubHeaders() });
  assert.equal(res.status, 401);
});

test('step 6: a GitHub request without X-GitHub-Delivery gets 400', async () => {
  const app = githubApp(recordingHandler());
  const res = await post(app, ping, { header: 'X-Hub-Signature-256', headers: { 'X-GitHub-Event': 'ping' } });
  assert.equal(res.status, 400);
});

test('step 6: a GitHub "Redeliver" (same delivery GUID) is a duplicate', async () => {
  const rec = recordingHandler();
  const app = githubApp(rec);
  await post(app, ping, { header: 'X-Hub-Signature-256', headers: githubHeaders('same-guid') });
  const again = await post(app, ping, { header: 'X-Hub-Signature-256', headers: githubHeaders('same-guid') });
  await app.locals.queue.onIdle();
  assert.equal(again.body.duplicate, true);
  assert.equal(rec.calls.length, 1);
});
