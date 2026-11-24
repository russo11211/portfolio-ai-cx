// Step 8 - contact-center events: call.ended -> CRM, lead.created -> dialer list.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { load, post, makeEvent, memoryLogger, SECRET } from './helpers.js';

const { createApp } = await load('app.js');
const { createEventHandler } = await load('handlers.js');
const { createMockCrm } = await load('crm.js');
const { createMockDialer } = await load('dialer.js');

function setup() {
  const crm = createMockCrm();
  const dialer = createMockDialer();
  const logger = memoryLogger();
  return { crm, dialer, logger, handleEvent: createEventHandler({ crm, dialer, logger }) };
}

const callEnded = (data = {}) =>
  makeEvent({
    type: 'call.ended',
    data: { callId: 'call-1', contactId: 'contact-42', disposition: 'SALE', durationSec: 183, agentId: 'agent-7', ...data },
  });

const leadCreated = (data = {}) =>
  makeEvent({
    type: 'lead.created',
    data: { leadId: 'lead-9', phone: '+5511999990000', name: 'Ana', campaign: 'cards-upsell', priority: 5, ...data },
  });

test('step 8: call.ended writes the disposition onto the CRM contact', async () => {
  const { crm, handleEvent } = setup();
  const event = callEnded();
  await handleEvent(event);
  const record = crm.get('contact-42');
  assert.equal(record.lastDisposition, 'SALE');
  assert.equal(record.callHistory.length, 1);
  assert.equal(record.callHistory[0].callId, 'call-1');
  assert.equal(record.callHistory[0].eventId, event.id);
});

test('step 8: a DO_NOT_CALL disposition flags the contact', async () => {
  const { crm, handleEvent } = setup();
  await handleEvent(callEnded({ disposition: 'DO_NOT_CALL' }));
  assert.equal(crm.get('contact-42').doNotCall, true);
});

test('step 8: call.ended without contactId or disposition throws (so it is logged as failed)', async () => {
  const { handleEvent } = setup();
  await assert.rejects(handleEvent(callEnded({ contactId: undefined })));
  await assert.rejects(handleEvent(callEnded({ disposition: undefined })));
});

test('step 8: lead.created enqueues the lead into its campaign dialer list, by priority', async () => {
  const { dialer, handleEvent } = setup();
  await handleEvent(leadCreated({ leadId: 'low', priority: 1 }));
  await handleEvent(leadCreated({ leadId: 'high', priority: 9 }));
  const list = dialer.list('cards-upsell');
  assert.deepEqual(list.map((l) => l.leadId), ['high', 'low']);
  assert.equal(list[0].phone, '+5511999990000');
});

test('step 8: lead.created without a campaign goes to the "default" list', async () => {
  const { dialer, handleEvent } = setup();
  await handleEvent(leadCreated({ campaign: undefined }));
  assert.equal(dialer.list('default').length, 1);
});

test('step 8: lead.created without a phone throws', async () => {
  const { handleEvent } = setup();
  await assert.rejects(handleEvent(leadCreated({ phone: undefined })));
});

test('step 8: an unknown event type is ignored and logged, not an error', async () => {
  const { logger, handleEvent } = setup();
  await handleEvent(makeEvent({ type: 'agent.status_changed' }));
  assert.ok(logger.entries.some((e) => e.msg === 'event.ignored'));
});

test('step 8: end to end - signed webhooks update the CRM and the dialer, duplicates do not double-dial', async () => {
  const crm = createMockCrm();
  const dialer = createMockDialer();
  const app = createApp({ secret: SECRET, logger: memoryLogger(), crm, dialer });

  await post(app, callEnded({ disposition: 'CALLBACK' }));
  const lead = leadCreated();
  await post(app, lead);
  const dup = await post(app, lead);
  await app.locals.queue.onIdle();

  assert.equal(crm.get('contact-42').lastDisposition, 'CALLBACK');
  assert.equal(dup.body.duplicate, true);
  assert.equal(dialer.list('cards-upsell').length, 1, 'a retried lead.created must not be dialed twice');
});
