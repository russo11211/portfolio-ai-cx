// Step 2 - HMAC-SHA256 signature verification.
// README: "Step 2". Run: npm run test:step2
import crypto from 'node:crypto'; // eslint-disable-line no-unused-vars

/**
 * Returns "sha256=<hex>" where <hex> is HMAC-SHA256(secret, rawBody).
 * Hint: crypto.createHmac('sha256', secret).update(rawBody).digest('hex')
 */
export function computeSignature(secret, rawBody) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 2): implement computeSignature');
}

/**
 * True only when `header` equals computeSignature(secret, rawBody).
 * - must NEVER throw (missing / malformed header => false)
 * - must use crypto.timingSafeEqual (and check lengths first: it throws on
 *   buffers of different length)
 */
export function verifySignature(secret, rawBody, header) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 2): implement verifySignature');
}
