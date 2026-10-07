// Step 4 - idempotency: the same event id is processed only once.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { load, post, makeEvent, memoryLogger, recordingHandler, SECRET } from './helpers.js';

const { createApp } = await load('app.js');
const { createMemoryStore } = await load('idempotency.js');

test('step 4: createMemoryStore.claim is true the first time, false after', async () => {
  const store = createMemoryStore();
  assert.equal(await store.claim('evt_1'), true);
  assert.equal(await store.claim('evt_1'), false);
  assert.equal(await store.claim('evt_2'), true);
});

test('step 4: release lets an id be claimed again (used to retry failures)', async () => {
  const store = createMemoryStore();
  await store.claim('evt_1');
  await store.release('evt_1');
  assert.equal(await store.claim('evt_1'), true);
});

test('step 4: a duplicate delivery gets 200 { duplicate: true } and is processed once', async () => {
  const rec = recordingHandler();
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: rec.handleEvent });
  const event = makeEvent();

  const first = await post(app, event);
  const second = await post(app, event);
  await app.locals.queue.onIdle();

  assert.equal(first.status, 200);
  assert.equal(first.body.duplicate, undefined);
  assert.equal(second.status, 200, 'a duplicate is still a 2xx, or the sender keeps retrying');
  assert.equal(second.body.duplicate, true);
  assert.equal(rec.calls.length, 1);
});

test('step 4: different ids are all processed', async () => {
  const rec = recordingHandler();
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: rec.handleEvent });
  await post(app, makeEvent());
  await post(app, makeEvent());
  await app.locals.queue.onIdle();
  assert.equal(rec.calls.length, 2);
});

test('step 4: the app uses the injected store (so it can be swapped for a database)', async () => {
  const rec = recordingHandler();
  const claimed = [];
  const store = {
    async claim(id) {
      claimed.push(id);
      return false; // pretend every event was already seen
    },
    async release() {},
  };
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: rec.handleEvent, store });
  const event = makeEvent();
  const res = await post(app, event);
  await app.locals.queue.onIdle();
  assert.equal(res.body.duplicate, true);
  assert.deepEqual(claimed, [event.id]);
  assert.equal(rec.calls.length, 0);
});

test('step 4: an event with a bad signature does not burn its id', async () => {
  const rec = recordingHandler();
  const app = createApp({ secret: SECRET, logger: memoryLogger(), handleEvent: rec.handleEvent });
  const event = makeEvent();
  await post(app, event, { secret: 'wrong' });
  const res = await post(app, event);
  await app.locals.queue.onIdle();
  assert.equal(res.body.duplicate, undefined);
  assert.equal(rec.calls.length, 1);
});
