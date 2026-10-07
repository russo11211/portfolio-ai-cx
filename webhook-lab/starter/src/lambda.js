// Step 7 - the same webhook as a native AWS Lambda handler
// (API Gateway HTTP API, payload format 2.0). README: "Step 7". Run: npm run test:step7
//
// createLambdaHandler({ secret, source = 'generic', logger, store, handleEvent })
// returns async (apiEvent) => ({ statusCode, headers, body }).
//   - method: apiEvent.requestContext.http.method   path: apiEvent.rawPath
//   - GET .../health -> 200; anything but POST .../webhook -> 404
//   - lowercase all header names before looking up the signature header
//   - rawBody = Buffer.from(apiEvent.body ?? '', apiEvent.isBase64Encoded ? 'base64' : 'utf8')
//   - same checks as the Express app: 401 / 400 / duplicate 200
//   - process INLINE (await handleEvent) - Lambda freezes after you return
//   - on failure: store.release(id), return 500 so the sender retries
// Do NOT import express here: the Lambda zip has no node_modules.
export function createLambdaHandler(options = {}) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 7): implement createLambdaHandler');
}

// The function AWS calls (handler setting: "src/lambda.handler").
// TODO(step 7): build the handler once from process.env (WEBHOOK_SECRET,
// WEBHOOK_SOURCE, LOG_LEVEL), cache it in a module variable, and delegate to it.
export async function handler(apiEvent, context) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 7): implement the exported Lambda handler');
}
