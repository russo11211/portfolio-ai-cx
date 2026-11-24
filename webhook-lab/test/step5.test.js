// Step 5 - structured logging, error handling, health endpoint.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import { load, post, makeEvent, memoryLogger, recordingHandler, SECRET } from './helpers.js';

const { createApp } = await load('app.js');
const { createLogger } = await load('logger.js');

test('step 5: createLogger writes one JSON object per line with time, level and msg', () => {
  const lines = [];
  const logger = createLogger({ write: (line) => lines.push(line) });
  logger.info('webhook.received', { eventId: 'evt_1' });
  assert.equal(lines.length, 1);
  const entry = JSON.parse(lines[0]);
  assert.equal(entry.level, 'info');
  assert.equal(entry.msg, 'webhook.received');
  assert.equal(entry.eventId, 'evt_1');
  assert.ok(!Number.isNaN(Date.parse(entry.time)));
});

test('step 5: createLogger respects the minimum level', () => {
  const lines = [];
  const logger = createLogger({ level: 'warn', write: (line) => lines.push(line) });
  logger.debug('a');
  logger.info('b');
  logger.warn('c');
  logger.error('d');
  assert.deepEqual(lines.map((l) => JSON.parse(l).msg), ['c', 'd']);
});

test('step 5: GET /health returns { status: "ok", queueDepth }', async () => {
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });
  const res = await request(app).get('/health');
  assert.equal(res.status, 200);
  assert.equal(res.body.status, 'ok');
  assert.equal(typeof res.body.queueDepth, 'number');
});

test('step 5: unknown routes get a JSON 404', async () => {
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });
  const res = await request(app).get('/nope');
  assert.equal(res.status, 404);
  assert.equal(res.body.error, 'not_found');
});

test('step 5: an oversized body gets a JSON 413', async () => {
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });
  const big = JSON.stringify(makeEvent({ data: { blob: 'x'.repeat(200 * 1024) } }));
  const res = await post(app, big);
  assert.equal(res.status, 413);
  assert.equal(res.body.error, 'payload_too_large');
});

test('step 5: a received event is logged with its id and type, never the secret or signature', async () => {
  const logger = memoryLogger();
  const app = createApp({ secret: SECRET, logger, handleEvent: recordingHandler().handleEvent });
  const event = makeEvent({ type: 'call.ended' });
  await post(app, event);
  await app.locals.queue.onIdle();
  const received = logger.entries.find((e) => e.msg === 'webhook.received');
  assert.ok(received, 'expected a "webhook.received" log entry');
  assert.equal(received.eventId, event.id);
  assert.equal(received.type, 'call.ended');
  const everything = JSON.stringify(logger.entries);
  assert.ok(!everything.includes(SECRET), 'the secret must never be logged');
  assert.ok(!everything.includes('sha256='), 'signatures must never be logged');
});

test('step 5: a rejected signature is logged as a warning', async () => {
  const logger = memoryLogger();
  const app = createApp({ secret: SECRET, logger, handleEvent: recordingHandler().handleEvent });
  await post(app, makeEvent(), { signature: null });
  assert.ok(logger.entries.some((e) => e.level === 'warn' && e.msg === 'webhook.rejected'));
});

test('step 5: a background failure is logged as "event.failed" (level error) with the event id', async () => {
  const logger = memoryLogger();
  const app = createApp({
    secret: SECRET,
    logger,
    handleEvent: async () => {
      throw new Error('CRM timeout');
    },
  });
  const event = makeEvent();
  await post(app, event);
  await app.locals.queue.onIdle();
  const failed = logger.entries.find((e) => e.msg === 'event.failed');
  assert.ok(failed, 'expected an "event.failed" log entry');
  assert.equal(failed.level, 'error');
  assert.equal(failed.eventId, event.id);
  assert.match(failed.error, /CRM timeout/);
});
