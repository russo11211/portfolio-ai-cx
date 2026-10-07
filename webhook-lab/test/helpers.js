// Shared test helpers. Tests run against starter/ by default (your code).
// Run against the reference solution with: npm run test:solution
// (or LAB_TARGET=solution npm run test:stepN).
import crypto from 'node:crypto';
import request from 'supertest';

export const TARGET = process.env.LAB_TARGET === 'solution' ? 'solution' : 'starter';
export const SECRET = 'test-secret';

/** Dynamically imports a module from starter/src or solution/src. */
export function load(moduleName) {
  return import(new URL(`../${TARGET}/src/${moduleName}`, import.meta.url));
}

/** Same algorithm a sender uses: "sha256=" + HMAC-SHA256(secret, rawBody) in hex. */
export function sign(rawBody, secret = SECRET) {
  return 'sha256=' + crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
}

/** A logger that records entries instead of printing them. */
export function memoryLogger() {
  const entries = [];
  const logger = { entries };
  for (const level of ['debug', 'info', 'warn', 'error']) {
    logger[level] = (msg, fields = {}) => entries.push({ level, msg, ...fields });
  }
  return logger;
}

let counter = 0;
export function makeEvent(overrides = {}) {
  counter += 1;
  return { id: `evt_${Date.now()}_${counter}`, type: 'test.ping', data: { hello: 'world' }, ...overrides };
}

/** A handler that records every event it receives. */
export function recordingHandler() {
  const calls = [];
  const handleEvent = async (event) => {
    calls.push(event);
  };
  return { calls, handleEvent };
}

/**
 * POSTs a webhook. `body` may be an object (JSON-encoded) or a raw string.
 * By default the request is correctly signed; pass `signature: null` to omit
 * the header or a string to send a specific (wrong) value.
 */
export function post(app, body, { signature, secret = SECRET, header = 'X-Signature-256', headers = {} } = {}) {
  const raw = typeof body === 'string' ? body : JSON.stringify(body);
  let req = request(app).post('/webhook').set('Content-Type', 'application/json');
  const sig = signature === undefined ? sign(raw, secret) : signature;
  if (sig !== null) req = req.set(header, sig);
  for (const [k, v] of Object.entries(headers)) req = req.set(k, v);
  return req.send(raw);
}

/** A promise you can resolve from the outside. */
export function deferred() {
  let resolve;
  const promise = new Promise((r) => {
    resolve = r;
  });
  return { promise, resolve };
}
