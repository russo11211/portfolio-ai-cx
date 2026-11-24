#!/usr/bin/env node
// Plays the role of the SENDER: builds an event, signs it with the shared
// secret and POSTs it to your receiver. It deliberately does not import
// anything from starter/ or solution/: a real sender is a different system.
//
// Usage:
//   WEBHOOK_SECRET=dev-secret node scripts/send-test-event.js [mode] [url]
//   npm run send -- duplicate
//
// Modes:
//   valid          a correctly signed test.ping event (default)
//   bad-signature  signed with the wrong secret            -> expect 401
//   no-signature   no signature header at all              -> expect 401
//   invalid-json   correctly signed, but not JSON          -> expect 400
//   duplicate      the same event sent twice               -> expect 200, then 200 { duplicate: true }
//   call-ended     a contact-center call.ended event       (step 8)
//   lead-created   a lead-distribution lead.created event  (step 8)
//
// Env: WEBHOOK_SECRET (required), WEBHOOK_URL (default http://localhost:3000/webhook)
import crypto from 'node:crypto';

const mode = process.argv[2] ?? 'valid';
const url = process.argv[3] ?? process.env.WEBHOOK_URL ?? 'http://localhost:3000/webhook';
const secret = process.env.WEBHOOK_SECRET;

if (!secret) {
  console.error('Set WEBHOOK_SECRET to the same value the receiver uses, e.g. export WEBHOOK_SECRET=dev-secret');
  process.exit(1);
}

const newId = () => `evt_${crypto.randomUUID()}`;
const sign = (raw, key = secret) => 'sha256=' + crypto.createHmac('sha256', key).update(raw).digest('hex');

const samples = {
  ping: () => ({ id: newId(), type: 'test.ping', data: { hello: 'world', sentAt: new Date().toISOString() } }),
  callEnded: () => ({
    id: newId(),
    type: 'call.ended',
    data: {
      callId: `call-${Date.now()}`,
      contactId: 'contact-42',
      disposition: 'CALLBACK',
      durationSec: 183,
      agentId: 'agent-7',
      endedAt: new Date().toISOString(),
    },
  }),
  leadCreated: () => ({
    id: newId(),
    type: 'lead.created',
    data: { leadId: `lead-${Date.now()}`, phone: '+5511999990000', name: 'Ana', campaign: 'cards-upsell', priority: 5 },
  }),
};

async function send(label, raw, signature) {
  const headers = { 'Content-Type': 'application/json' };
  if (signature) headers['X-Signature-256'] = signature;
  const started = performance.now();
  const res = await fetch(url, { method: 'POST', headers, body: raw });
  const ms = Math.round(performance.now() - started);
  const text = await res.text();
  console.log(`${label.padEnd(14)} -> ${res.status} in ${ms} ms  ${text}`);
}

try {
  switch (mode) {
    case 'valid': {
      const raw = JSON.stringify(samples.ping());
      await send('valid', raw, sign(raw));
      break;
    }
    case 'bad-signature': {
      const raw = JSON.stringify(samples.ping());
      await send('bad-signature', raw, sign(raw, 'not-the-secret'));
      break;
    }
    case 'no-signature': {
      await send('no-signature', JSON.stringify(samples.ping()), null);
      break;
    }
    case 'invalid-json': {
      const raw = '{"id": "evt_broken", "type": ';
      await send('invalid-json', raw, sign(raw));
      break;
    }
    case 'duplicate': {
      const raw = JSON.stringify(samples.ping());
      await send('1st delivery', raw, sign(raw));
      await send('2nd delivery', raw, sign(raw));
      break;
    }
    case 'call-ended': {
      const raw = JSON.stringify(samples.callEnded());
      await send('call.ended', raw, sign(raw));
      break;
    }
    case 'lead-created': {
      const raw = JSON.stringify(samples.leadCreated());
      await send('lead.created', raw, sign(raw));
      break;
    }
    default:
      console.error(`Unknown mode "${mode}". See the header of this file for the list.`);
      process.exit(1);
  }
} catch (err) {
  console.error(`Could not reach ${url}: ${err.cause?.code ?? err.message}. Is the server running?`);
  process.exit(1);
}
