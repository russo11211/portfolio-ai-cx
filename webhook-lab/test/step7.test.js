// Step 7 - native AWS Lambda handler (API Gateway HTTP API, payload v2.0).
// These tests call the handler function directly with a fake API Gateway event:
// no AWS account needed.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { load, sign, makeEvent, memoryLogger, recordingHandler, SECRET } from './helpers.js';

const { createLambdaHandler } = await load('lambda.js');

function apiGatewayEvent(body, { method = 'POST', path = '/webhook', headers, base64 = false } = {}) {
  const raw = typeof body === 'string' ? body : JSON.stringify(body);
  return {
    version: '2.0',
    rawPath: path,
    requestContext: { http: { method, path } },
    headers: headers ?? { 'content-type': 'application/json', 'x-signature-256': sign(raw) },
    body: base64 ? Buffer.from(raw).toString('base64') : raw,
    isBase64Encoded: base64,
  };
}

const newHandler = (handleEvent) =>
  createLambdaHandler({ secret: SECRET, logger: memoryLogger(), handleEvent: handleEvent ?? recordingHandler().handleEvent });

test('step 7: a signed event returns statusCode 200 and is processed BEFORE the handler returns', async () => {
  const rec = recordingHandler();
  const handler = newHandler(rec.handleEvent);
  const result = await handler(apiGatewayEvent(makeEvent()));
  assert.equal(result.statusCode, 200);
  assert.equal(JSON.parse(result.body).received, true);
  assert.equal(rec.calls.length, 1, 'Lambda freezes after returning, so process inline');
});

test('step 7: a bad signature returns 401', async () => {
  const handler = newHandler();
  const event = apiGatewayEvent(makeEvent(), { headers: { 'x-signature-256': 'sha256=' + '0'.repeat(64) } });
  const result = await handler(event);
  assert.equal(result.statusCode, 401);
});

test('step 7: a base64-encoded body is decoded before verifying', async () => {
  const handler = newHandler();
  const result = await handler(apiGatewayEvent(makeEvent(), { base64: true }));
  assert.equal(result.statusCode, 200);
});

test('step 7: header names are matched case-insensitively (REST API v1 keeps the original case)', async () => {
  const body = JSON.stringify(makeEvent());
  const handler = newHandler();
  const result = await handler(apiGatewayEvent(body, { headers: { 'X-Signature-256': sign(body) } }));
  assert.equal(result.statusCode, 200);
});

test('step 7: a duplicate returns 200 with duplicate: true', async () => {
  const rec = recordingHandler();
  const handler = newHandler(rec.handleEvent);
  const event = makeEvent();
  await handler(apiGatewayEvent(event));
  const second = await handler(apiGatewayEvent(event));
  assert.equal(second.statusCode, 200);
  assert.equal(JSON.parse(second.body).duplicate, true);
  assert.equal(rec.calls.length, 1);
});

test('step 7: a processing failure returns 500 and the retry is processed', async () => {
  let attempts = 0;
  const handler = newHandler(async () => {
    attempts += 1;
    if (attempts === 1) throw new Error('CRM timeout');
  });
  const event = makeEvent();
  const first = await handler(apiGatewayEvent(event));
  assert.equal(first.statusCode, 500, 'tell the sender to retry');
  const retry = await handler(apiGatewayEvent(event));
  assert.equal(retry.statusCode, 200);
  assert.equal(JSON.parse(retry.body).duplicate, undefined, 'the failed attempt must not count as processed');
  assert.equal(attempts, 2);
});

test('step 7: GET /health returns 200 and unknown routes 404', async () => {
  const handler = newHandler();
  const health = await handler(apiGatewayEvent('', { method: 'GET', path: '/health' }));
  assert.equal(health.statusCode, 200);
  const missing = await handler(apiGatewayEvent('', { method: 'GET', path: '/other' }));
  assert.equal(missing.statusCode, 404);
});
