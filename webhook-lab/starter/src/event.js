// Step 1 (parseJson) and Step 6 (SOURCES / getSource).

// TODO(step 1): parse the raw body.
// Return { ok: true, value } on success or { ok: false } on invalid JSON.
// Never throw. Hint: rawBody is a Buffer -> rawBody.toString('utf8').
export function parseJson(rawBody) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 1): implement parseJson');
}

// TODO(step 1): the generic source. toEvent(body) returns { id, type, data }
// when body is a plain object with string `id` and `type`, otherwise null.
// TODO(step 6): add a `github` source: signature header 'x-hub-signature-256',
// id from headers['x-github-delivery'], type `github.${headers['x-github-event']}`,
// data = the whole body.
export const SOURCES = {
  generic: {
    signatureHeader: 'x-signature-256',
    toEvent(body, headers) { // eslint-disable-line no-unused-vars
      throw new Error('TODO(step 1): implement SOURCES.generic.toEvent');
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
