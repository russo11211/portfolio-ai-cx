// Step 3 - acknowledge fast, process asynchronously through a queue.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { load, post, makeEvent, memoryLogger, deferred, SECRET } from './helpers.js';

const { createApp } = await load('app.js');
const { createQueue } = await load('queue.js');

test('step 3: the response is sent BEFORE the event finishes processing', async () => {
  const gate = deferred();
  const processed = [];
  const handleEvent = async (event) => {
    await gate.promise; // simulate a slow CRM call that has not answered yet
    processed.push(event.id);
  };
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent });
  const event = makeEvent();

  const res = await post(app, event);
  assert.equal(res.status, 200);
  assert.deepEqual(processed, [], 'the handler must still be waiting when the sender gets its 200');

  gate.resolve();
  await app.locals.queue.onIdle();
  assert.deepEqual(processed, [event.id]);
});

test('step 3: the worker receives the normalized event { id, type, data }', async () => {
  const seen = [];
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: async (e) => seen.push(e) });
  const event = makeEvent({ type: 'call.started', data: { callId: 'c-1' } });
  await post(app, event);
  await app.locals.queue.onIdle();
  assert.deepEqual(seen, [{ id: event.id, type: 'call.started', data: { callId: 'c-1' } }]);
});

test('step 3: a failing handler does not change the response or crash the app', async () => {
  const app = createApp({
    secret: SECRET,
    logger: memoryLogger(),
    handleEvent: async () => {
      throw new Error('CRM is down');
    },
  });
  const res = await post(app, makeEvent());
  assert.equal(res.status, 200);
  await app.locals.queue.onIdle();
  const again = await post(app, makeEvent());
  assert.equal(again.status, 200);
  await app.locals.queue.onIdle();
});

test('step 3: createQueue processes jobs in order and reports depth', async () => {
  const done = [];
  const queue = createQueue({ worker: async (job) => done.push(job) });
  queue.enqueue(1);
  queue.enqueue(2);
  queue.enqueue(3);
  assert.equal(queue.depth, 3);
  await queue.onIdle();
  assert.deepEqual(done, [1, 2, 3]);
  assert.equal(queue.depth, 0);
});

test('step 3: createQueue calls onError and keeps going after a failing job', async () => {
  const errors = [];
  const done = [];
  const queue = createQueue({
    worker: async (job) => {
      if (job === 'bad') throw new Error('boom');
      done.push(job);
    },
    onError: (err, job) => errors.push([err.message, job]),
  });
  queue.enqueue('bad');
  queue.enqueue('good');
  await queue.onIdle();
  assert.deepEqual(errors, [['boom', 'bad']]);
  assert.deepEqual(done, ['good']);
});
