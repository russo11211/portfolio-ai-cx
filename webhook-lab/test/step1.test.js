// Step 1 - POST /webhook parses JSON and answers 200; 400 on invalid input.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import { load, post, makeEvent, memoryLogger, recordingHandler, SECRET } from './helpers.js';

const { createApp } = await load('app.js');
const newApp = () => createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: recordingHandler().handleEvent });

test('step 1: a valid JSON event gets 200 { received: true }', async () => {
  const res = await post(newApp(), makeEvent());
  assert.equal(res.status, 200);
  assert.equal(res.body.received, true);
});

test('step 1: the response is JSON', async () => {
  const res = await post(newApp(), makeEvent());
  assert.match(res.headers['content-type'] ?? '', /application\/json/);
});

test('step 1: invalid JSON gets 400 { error: "invalid_json" }', async () => {
  const res = await post(newApp(), '{"id": "evt_1", "type": ');
  assert.equal(res.status, 400);
  assert.equal(res.body.error, 'invalid_json');
});

test('step 1: JSON without id or type gets 400 { error: "invalid_event" }', async () => {
  const noId = await post(newApp(), { type: 'test.ping' });
  assert.equal(noId.status, 400);
  assert.equal(noId.body.error, 'invalid_event');
  const noType = await post(newApp(), { id: 'evt_x' });
  assert.equal(noType.status, 400);
  const notObject = await post(newApp(), '[1,2,3]');
  assert.equal(notObject.status, 400);
});

test('step 1: GET /webhook is not a webhook (404)', async () => {
  const res = await request(newApp()).get('/webhook');
  assert.equal(res.status, 404);
});
