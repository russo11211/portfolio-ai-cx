// Step 2 - HMAC-SHA256 signature verification.
//
// The sender and the receiver share a secret. The sender computes
// HMAC-SHA256(secret, rawBody) and sends it in a header as "sha256=<hex>".
// We recompute it over the EXACT bytes we received and compare.
import crypto from 'node:crypto';

const PREFIX = 'sha256=';

/** Returns "sha256=<hex>" for the given raw body (Buffer or string). */
export function computeSignature(secret, rawBody) {
  const hex = crypto.createHmac('sha256', secret).update(rawBody).digest('hex');
  return PREFIX + hex;
}

/**
 * True only when `header` is a valid "sha256=<hex>" signature of `rawBody`.
 * Never throws: a missing or malformed header is simply `false`.
 */
export function verifySignature(secret, rawBody, header) {
  if (!secret || typeof header !== 'string' || !header.startsWith(PREFIX)) {
    return false;
  }
  const expected = Buffer.from(computeSignature(secret, rawBody), 'utf8');
  const received = Buffer.from(header, 'utf8');
  // timingSafeEqual throws if lengths differ, so check length first.
  // Leaking "the length was wrong" is harmless: the length of a SHA-256 hex
  // digest is public knowledge (71 chars with the prefix).
  if (expected.length !== received.length) {
    return false;
  }
  // Constant-time comparison: the time taken does not depend on how many
  // leading characters match, so an attacker cannot guess byte by byte.
  return crypto.timingSafeEqual(expected, received);
}
