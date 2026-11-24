// Step 2 - HMAC-SHA256 over the RAW body, constant-time comparison.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { load, post, sign, makeEvent, memoryLogger, recordingHandler, SECRET } from './helpers.js';

const { verifySignature, computeSignature } = await load('signature.js');
const { createApp } = await load('app.js');

test('step 2: computeSignature returns "sha256=<64 hex chars>"', () => {
  const sig = computeSignature(SECRET, Buffer.from('{"a":1}'));
  assert.match(sig, /^sha256=[0-9a-f]{64}$/);
  assert.equal(sig, sign('{"a":1}'));
});

test('step 2: verifySignature accepts a correct signature', () => {
  const body = Buffer.from('{"id":"evt_1","type":"test.ping"}');
  assert.equal(verifySignature(SECRET, body, sign(body)), true);
});

test('step 2: verifySignature rejects wrong secret, missing and malformed headers without throwing', () => {
  const body = Buffer.from('{"id":"evt_1"}');
  assert.equal(verifySignature(SECRET, body, sign(body, 'other-secret')), false);
  assert.equal(verifySignature(SECRET, body, undefined), false);
  assert.equal(verifySignature(SECRET, body, ''), false);
  assert.equal(verifySignature(SECRET, body, 'sha256=abc'), false);
  assert.equal(verifySignature(SECRET, body, sign(body).replace('sha256=', 'md5=')), false);
  assert.equal(verifySignature(SECRET, body, sign(body).toUpperCase()), false);
});

test('step 2: a request with no signature gets 401 and is not processed', async () => {
  const rec = recordingHandler();
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: rec.handleEvent });
  const res = await post(app, makeEvent(), { signature: null });
  assert.equal(res.status, 401);
  assert.equal(res.body.error, 'invalid_signature');
  await app.locals.queue?.onIdle?.();
  assert.equal(rec.calls.length, 0);
});

test('step 2: a request signed with the wrong secret gets 401', async () => {
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });
  const res = await post(app, makeEvent(), { secret: 'attacker-guess' });
  assert.equal(res.status, 401);
});

test('step 2: the signature is checked on the RAW bytes (pretty-printed JSON still verifies)', async () => {
  // If you verified JSON.stringify(parsedBody) instead of the raw bytes, the
  // whitespace would be gone and this valid request would fail.
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });
  const pretty = JSON.stringify(makeEvent({ data: { name: 'João' } }), null, 2);
  const res = await post(app, pretty);
  assert.equal(res.status, 200);
});

test('step 2: a tampered body fails even with the original signature', async () => {
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });
  const original = JSON.stringify(makeEvent({ data: { amount: 10 } }));
  const tampered = original.replace('10', '99');
  const res = await post(app, tampered, { signature: sign(original) });
  assert.equal(res.status, 401);
});

test('step 2: authentication comes before parsing (bad signature + bad JSON = 401, not 400)', async () => {
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });
  const res = await post(app, '{not json', { signature: 'sha256=' + '0'.repeat(64) });
  assert.equal(res.status, 401);
});
