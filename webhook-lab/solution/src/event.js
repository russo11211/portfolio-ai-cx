// Step 1 (parsing) and Step 6 (sources).
//
// A "source" describes one kind of sender: which header carries the
// signature and how to turn its payload into our internal event shape
// { id, type, data }.

export const SOURCES = {
  // Our own generic format: the id and type travel in the JSON body.
  generic: {
    signatureHeader: 'x-signature-256',
    toEvent(body) {
      if (!isObject(body) || typeof body.id !== 'string' || typeof body.type !== 'string') {
        return null;
      }
      return { id: body.id, type: body.type, data: body.data ?? {} };
    },
  },
  // GitHub: the id and type travel in HTTP headers, the body is the payload.
  github: {
    signatureHeader: 'x-hub-signature-256',
    toEvent(body, headers) {
      const id = headers['x-github-delivery'];
      const name = headers['x-github-event'];
      if (!isObject(body) || !id || !name) {
        return null;
      }
      return { id, type: `github.${name}`, data: body };
    },
  },
};

export function getSource(name = 'generic') {
  const source = SOURCES[name];
  if (!source) {
    throw new Error(`Unknown webhook source "${name}". Use one of: ${Object.keys(SOURCES).join(', ')}`);
  }
  return source;
}

/** Parses a raw body. Returns { ok: true, value } or { ok: false }. Never throws. */
export function parseJson(rawBody) {
  try {
    return { ok: true, value: JSON.parse(rawBody.toString('utf8')) };
  } catch {
    return { ok: false };
  }
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
