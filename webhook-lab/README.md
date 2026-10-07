# webhook-lab: build a webhook receiver from scratch

A guided, test-driven tutorial. You build, line by line, the kind of webhook
endpoint that sits between a contact-center platform, a CRM and a dialer:

```
 sender (GitHub, a CCaaS platform, a lead source...)
    |  POST /webhook   X-Signature-256: sha256=<hmac>
    v
 [ raw bytes ] -> verify HMAC -> parse JSON -> validate -> dedupe by id -> enqueue -> 200 (fast)
                                                                              |
                                                     worker (background) <----+
                                                       call.ended   -> CRM record
                                                       lead.created -> dialer list
```

By the end you can explain every line out loud in a technical interview, and
you have the same code running locally, receiving real GitHub webhooks, and
deployed as an AWS Lambda behind API Gateway.

> Tutorial scaffold, tests and reference solution generated with **Claude Code**.
> The code in `starter/` is meant to be written by you, by hand.

## How the lab works

```
webhook-lab/
├── starter/src/      <- YOUR code. Skeleton + TODO(step N) comments.
├── solution/src/     <- reference implementation. Try first; open only when stuck.
├── test/             <- step1.test.js ... step8.test.js (shared by both)
├── scripts/send-test-event.js   <- plays the sender: signs and POSTs events
└── package.json
```

- The tests run against **`starter/`** by default, so they fail until you
  implement each step. That is expected: red first, then green.
- `npm run test:stepN` runs one step. `npm test` runs all of them.
- `npm run test:solution` runs everything against `solution/` (all green). To
  check one step of the solution: `LAB_TARGET=solution npm run test:step3`.
- `solution/` is the answer key. Each step below says which solution file to
  compare with **after** you are green, not before.

Requirements: Node.js 20 or newer (`node --version`), npm, git. Step 6 needs a
GitHub repository you own; step 7 needs an AWS account (optional).

```bash
cd webhook-lab
npm install
npm run test:step1      # red: this is your starting point
```

---

## Step 1 - Receive a POST and parse JSON

**Goal.** `POST /webhook` answers `200 {"received": true}` for a valid event,
`400 {"error": "invalid_json"}` when the body is not JSON, and
`400 {"error": "invalid_event"}` when it is JSON but lacks a string `id` and `type`.

**Concept.** A webhook is just an HTTP request that *another system* sends to
you when something happens ("a call ended", "a lead was created"). You do not
poll; they push. Your side is an ordinary HTTP endpoint with three jobs:
accept the request, decide whether it is trustworthy and well-formed, and tell
the sender "got it" with a status code. The status code is the whole contract:
`2xx` means "delivered, stop sending"; anything else means "failed", and many
senders will retry.

Our internal event shape is always `{ id, type, data }`. `id` identifies one
delivery (step 4 depends on it); `type` decides what to do (step 8).

We read the body with `express.raw()`, not `express.json()`. `express.raw()`
gives us a `Buffer` with the exact bytes received. We parse it ourselves with
`JSON.parse` inside a `try/catch`. Step 2 explains why the raw bytes matter.

**Build.**
1. `starter/src/event.js`: implement `parseJson(rawBody)` (returns
   `{ ok: true, value }` or `{ ok: false }`, never throws) and
   `SOURCES.generic.toEvent(body)` (returns `{ id, type, data }` or `null`).
2. `starter/src/app.js`: add `app.post('/webhook', express.raw({ type: '*/*', limit: '100kb' }), handler)`.
   In the handler: `parseJson(req.body)`, then `toEvent`, then `res.status(200).json({ received: true })`.
   Watch out: when there is no body at all, `req.body` may not be a Buffer.
   `Buffer.isBuffer(req.body) ? req.body : Buffer.alloc(0)` covers it.

**Checkpoint.** `npm run test:step1` is green. Then try it by hand:

```bash
export WEBHOOK_SECRET=dev-secret
npm start                                   # terminal 1
curl -i -X POST localhost:3000/webhook \
  -H 'Content-Type: application/json' \
  -d '{"id":"evt_1","type":"test.ping","data":{}}'   # terminal 2
```

Compare with: `solution/src/event.js` (`parseJson`, `SOURCES.generic`).

**Explain it out loud.**
- *What is a webhook, compared with polling an API?* A webhook is a push: the
  provider calls my HTTP endpoint when an event happens. Polling means I keep
  asking "anything new?", which wastes calls and adds latency. Webhooks are
  near real-time and cheaper, but now I must run a public, reliable endpoint.
- *Why return 400 for invalid JSON instead of 500?* 4xx means "your request is
  wrong, retrying the same thing will not help"; 5xx means "I failed, try
  again later". Malformed input is the sender's problem, so 400.
- *Why validate `id` and `type` at the edge?* So everything behind the
  endpoint can trust the shape `{ id, type, data }`. Fail fast at the boundary
  instead of crashing deep inside the business logic.

---

## Step 2 - Verify an HMAC-SHA256 signature on the raw body

**Goal.** Reject anything that was not signed with our shared secret:
`401 {"error": "invalid_signature"}` for a missing, malformed or wrong
`X-Signature-256: sha256=<hex>` header. Verify **before** parsing.

**Concept.** Your URL is public. Anyone who finds it can POST a fake
`lead.created`. The fix is a *shared secret*: sender and receiver both know
it, nobody else does. For every delivery the sender computes

```
signature = "sha256=" + hex( HMAC-SHA256(key = secret, message = raw request body) )
```

and sends it in a header. You recompute it over the bytes you received and
compare. If someone changes one byte of the body, or does not know the secret,
the values will not match. HMAC proves two things: **authenticity** (it came
from someone holding the secret) and **integrity** (the body was not changed
on the way).

**Why the RAW body.** The signature is computed over *bytes*, not over "the
JSON". `{"a":1}` and `{ "a": 1 }` are the same JSON but different bytes, so
different signatures. If you let a JSON parser build an object and then
`JSON.stringify` it again to verify, whitespace, key order, number formatting
(`1.0` becomes `1`) and unicode escaping (`ã` becomes `ã`) can all change,
and a perfectly valid request fails. That is why step 1 used `express.raw()`.
One of the step 2 tests sends pretty-printed JSON to catch exactly this.

**Why `crypto.timingSafeEqual`.** A normal `===` on strings stops at the first
different character, so it returns slightly faster the earlier the mismatch.
In theory an attacker can measure that and discover the correct signature one
character at a time (a *timing attack*). `timingSafeEqual` always compares
every byte. It throws if the two buffers have different lengths, so check the
length first (the length of a SHA-256 hex digest is not a secret).

**Why verify before parsing.** Unauthenticated requests should get as little
work and information as possible. A stranger should learn "401", not "your
JSON is broken at position 12".

**Build.**
1. `starter/src/signature.js`: `computeSignature(secret, rawBody)` and
   `verifySignature(secret, rawBody, header)` (never throws, returns a boolean).
2. `starter/src/app.js`: read `req.get('x-signature-256')` and call
   `verifySignature(options.secret, rawBody, header)` as the first thing in the
   handler.

**Checkpoint.** `npm run test:step2`. By hand (server running):

```bash
node scripts/send-test-event.js valid           # 200
node scripts/send-test-event.js bad-signature   # 401
node scripts/send-test-event.js no-signature    # 401
```

Compare with: `solution/src/signature.js`.

**Explain it out loud.**
- *How do you know a webhook really came from the provider?* We share a secret
  with the provider; it signs each body with HMAC-SHA256 and sends the
  signature in a header. I recompute the HMAC over the raw bytes and compare
  in constant time. No match, 401, nothing processed.
- *Why must you verify the raw body and not the parsed JSON?* The signature
  covers bytes. Re-serializing parsed JSON can change whitespace, key order,
  numbers and escaping, so a valid request would fail. Keep the original
  buffer until verification is done.
- *Why not just compare the strings with `===`?* String comparison can leak
  through timing how many leading characters matched. `timingSafeEqual` takes
  the same time regardless. (HMAC vs a plain hash: a plain SHA-256 of the body
  can be computed by anyone; HMAC needs the secret.)

---

## Step 3 - Acknowledge fast, process asynchronously

**Goal.** Answer `200` immediately and do the real work afterwards, through an
in-memory queue and a worker. A failure in the worker must not crash the
process or change the response.

**Concept.** Senders wait only a short time for your answer. GitHub, for
example, expects a 2xx within 10 seconds. If you do slow work inside the
request (a CRM API call that hangs, a database under load), the sender times
out, marks the delivery as failed and, depending on the provider, **retries**:
often with exponential backoff, sometimes for hours or days. Now you receive
the same event again while the first one may still be running. Slow handlers
create duplicates and retry storms.

The pattern is **ack fast, process later**: validate, store/enqueue, return
2xx in milliseconds, and let a worker do the slow part. Some APIs use `202
Accepted` to say "accepted, not yet processed"; most webhook senders treat any
2xx as success, and we use `200` throughout.

The trade-off you must be able to name: once you answered 2xx, the sender will
not retry. If your worker fails, **you** own the retry (a dead-letter queue,
an alert, a re-processing job). And our queue lives in memory: if the process
dies, queued events are lost. Production systems use a durable queue (SQS,
RabbitMQ, a database table) for that reason. Step 7 shows the AWS version.

**Build.**
1. `starter/src/queue.js`: `createQueue({ worker, concurrency = 1, onError })`
   with `enqueue(job)`, `onIdle()` and a `depth` getter. Start work with
   `setImmediate(pump)` so it runs after the response is sent; wrap each job in
   `Promise.resolve().then(() => worker(job)).catch(...).finally(...)`.
2. `starter/src/app.js`: create the queue with
   `worker: (event) => options.handleEvent(event)`, store it in
   `app.locals.queue`, and replace "respond" with "enqueue, then respond".

**Checkpoint.** `npm run test:step3`. The first test proves the response
arrives while the handler is still blocked on a promise.

Compare with: `solution/src/queue.js`, the `createQueue` block in `solution/src/app.js`.

**Explain it out loud.**
- *Why not process the event inside the HTTP request?* Senders have short
  timeouts and retry on failure. Slow processing turns into timeouts, which
  turn into duplicate deliveries. I acknowledge in milliseconds and process in
  the background.
- *What do you lose by acknowledging first?* The sender's retry. If processing
  fails after the 2xx, I have to retry myself: durable queue, dead-letter
  queue, alerting. With an in-memory queue I also lose events on a crash,
  which is why production uses SQS or similar.
- *What happens to in-flight events on deploy?* On SIGTERM the server stops
  accepting connections and waits for the queue to drain (`onIdle()`) before
  exiting. See `solution/src/server.js`.

---

## Step 4 - Idempotency: never process the same event twice

**Goal.** Deduplicate by event `id`. The second delivery of the same id gets
`200 {"received": true, "duplicate": true}` and is **not** processed again.

**Concept.** Webhook delivery is *at least once*, not *exactly once*. Retries
after a timeout, a manual "Redeliver" button, a network blip after you
answered: the same event can arrive two or more times. *Idempotent* means
processing it twice has the same effect as processing it once. Without it, a
retried `lead.created` dials the same customer twice.

The tool is an **idempotency key**: the event id. Before enqueuing, try to
*claim* it. First time: proceed. Already seen: answer 2xx (it *was*
delivered, so the sender must stop retrying) and do nothing.

Two details interviewers like:
- **Check-and-set must be atomic.** "if not seen, then mark as seen" as two
  separate steps lets two concurrent deliveries both pass the check. With a
  `Set` in one Node.js process it is atomic by nature (single thread, no
  `await` between `has` and `add`). In a database, use one atomic operation:
  a unique constraint, `INSERT ... ON CONFLICT DO NOTHING`, or a conditional
  write (step 7).
- **Only claim after authenticating.** Otherwise an attacker could burn real
  ids with unsigned requests. A test checks this.

Memory is not forever: a real store keeps ids for a window (for example 7 days
with a TTL), longer than the sender's retry window.

*Optional: SQLite.* To survive restarts on a single machine, the same
`claim(id)` interface can be backed by SQLite: a table `processed_events(id
TEXT PRIMARY KEY, received_at TEXT)` and `INSERT OR IGNORE INTO
processed_events ...`; if the statement changed 0 rows, it is a duplicate.
Recent Node.js versions ship a built-in `node:sqlite` module (still marked
experimental), or use the `better-sqlite3` package. Not required for the tests.

**Build.**
1. `starter/src/idempotency.js`: `createMemoryStore()` with async
   `claim(id)` and `release(id)`.
2. `starter/src/app.js`: `const { store = createMemoryStore() } = options;`
   then `await store.claim(event.id)` after validation, before enqueue.

**Checkpoint.** `npm run test:step4`. By hand:

```bash
node scripts/send-test-event.js duplicate
# 1st delivery   -> 200  {"received":true}
# 2nd delivery   -> 200  {"received":true,"duplicate":true}
```

Compare with: `solution/src/idempotency.js`.

**Explain it out loud.**
- *What does idempotent mean for a webhook consumer?* Receiving the same event
  N times has the same effect as once. Delivery is at-least-once, so I dedupe
  on the event id with an atomic check-and-set.
- *Why answer 200 to a duplicate instead of 409?* From the sender's view it was
  delivered. A non-2xx makes it retry, which creates more duplicates.
- *Where would you store the ids in production?* A store with an atomic
  conditional write and a TTL: DynamoDB conditional put, Redis `SET NX EX`, or
  a unique key in Postgres. Not process memory, which disappears on restart
  and is not shared across instances.

---

## Step 5 - Structured logging, error handling, health check

**Goal.**
- `createLogger()` writes one JSON object per line: `time`, `level`, `msg`, plus fields.
- Log `webhook.received` (with `eventId` and `type`), `webhook.rejected`
  (warn), `webhook.duplicate`, and `event.failed` (error) when the worker throws.
- `GET /health` returns `{ "status": "ok", "queueDepth": <n> }`.
- Unknown routes get a JSON `404 {"error": "not_found"}`; a body over 100 kb
  gets a JSON `413 {"error": "payload_too_large"}`.

**Concept.** At 3 a.m. the question is "did event `evt_123` arrive, and what
happened to it?". Plain text logs answer that with `grep`; structured JSON
logs answer it with a query in CloudWatch, Datadog or Loki
(`eventId = "evt_123"`). Log identifiers and outcomes, **never** the secret,
the signature, or full payloads (contact-center payloads carry phone numbers,
names, sometimes card or ID data).

Error handling has two layers. In the request: an Express *error middleware*
(a function with four arguments `(err, req, res, next)`) turns any thrown
error, including the body-size error from `express.raw`, into a clean JSON
response. In the background: the queue's `onError` logs failures, because
nobody is waiting for that promise and an unhandled rejection can crash Node.

The health endpoint is for load balancers and uptime monitors. Keep it cheap
and unauthenticated, and expose something useful for operations (queue depth).

**Build.**
1. `starter/src/logger.js`: `createLogger({ level, write, base })`.
2. `starter/src/app.js`: `const { logger = createLogger() } = options;`, the
   log calls, `GET /health`, a final `app.use((req, res) => 404)`, then the
   error middleware (`err.status === 413` for the size limit).

**Checkpoint.** `npm run test:step5`. By hand: `curl localhost:3000/health`,
then watch the JSON lines in the server terminal while you run the sender.

Compare with: `solution/src/logger.js`, end of `solution/src/app.js`.

**Explain it out loud.**
- *What do you log for a webhook, and what do you never log?* Event id, type,
  outcome, latency, rejection reasons. Never secrets, signatures, tokens or
  raw payloads with personal data.
- *Why structured logs?* They are machine-queryable: filter by `eventId`,
  count `event.failed` per type, alert on spikes. Trace one event from receipt
  to processing.
- *How do you handle an error thrown in the background worker?* Catch it at
  the queue, log it with the event id at error level, and route it to a retry
  or dead-letter path. Never let it become an unhandled rejection.

---

## Step 6 - A real sender: GitHub webhooks

**Goal.** Run the same receiver in "GitHub mode" and receive real deliveries
from a GitHub repository through a public tunnel. GitHub signs with the header
**`X-Hub-Signature-256`** (same `sha256=<hex>` format), sends the event name in
`X-GitHub-Event` and a unique delivery GUID in `X-GitHub-Delivery`.

**Concept.** Every provider uses the same idea with different details: header
name, how the id and type are sent, sometimes a timestamp in the signed
string to stop replays. Good code isolates those details in one place. Here a
**source** object holds them:

```js
github: {
  signatureHeader: 'x-hub-signature-256',
  toEvent(body, headers) {
    // id and type come from headers, the body is the payload
    return { id: headers['x-github-delivery'], type: `github.${headers['x-github-event']}`, data: body };
  },
}
```

Signature verification does not change at all. Idempotency comes for free:
GitHub's "Redeliver" button resends with the **same** `X-GitHub-Delivery`, so
it is reported as a duplicate. Also note: GitHub does not retry failed
deliveries automatically; you redeliver from the UI or API.

**Build.**
1. `starter/src/event.js`: add `SOURCES.github` as above.
2. `starter/src/app.js`: `const source = getSource(options.source)` and use
   `source.signatureHeader` and `source.toEvent(parsed.value, req.headers)`.

**Checkpoint.** `npm run test:step6`. Then the real thing:

1. Start the receiver in GitHub mode with a secret you will paste into GitHub:
   ```bash
   export WEBHOOK_SECRET="$(openssl rand -hex 32)"; echo "$WEBHOOK_SECRET"
   WEBHOOK_SOURCE=github npm start
   ```
2. Open a public tunnel to `localhost:3000` (pick one):
   - **smee.io** (no account): open https://smee.io, click *Start a new
     channel*, copy the URL, then
     `npx smee-client --url https://smee.io/<your-channel> --target http://localhost:3000/webhook`.
   - **ngrok** (free account + authtoken): `ngrok http 3000`, copy the
     `https://...` forwarding URL and append `/webhook`.
3. In a repository you own: *Settings > Webhooks > Add webhook*.
   - Payload URL: the smee channel URL, or the ngrok URL + `/webhook`.
   - **Content type: `application/json`** (the default form encoding would
     send `payload=...`, which our JSON parser rejects with 400).
   - Secret: the value you printed in step 1.
   - Events: *Just the push event* is enough.
4. GitHub immediately sends a `ping`. Check *Recent Deliveries* (status 200)
   and the `webhook.received` line with `type: "github.ping"` in your terminal.
   Push a commit to see `github.push`. Click *Redeliver* and see `webhook.duplicate`.

If deliveries arrive but fail with 401 only through a proxy, compare the
bytes: any tool in the middle that re-serializes the JSON breaks the
signature. That is the step 2 lesson in real life. Try the other tunnel.

Compare with: `SOURCES.github` in `solution/src/event.js`.

**Explain it out loud.**
- *How would you add a second provider?* Isolate per-provider details
  (signature header and scheme, where id and type live) in an adapter that
  normalizes to one internal event shape. Verification, dedupe, queue and
  business logic stay the same.
- *How do you test a webhook locally?* Unit tests that sign fake requests
  (like `test/`), a script that plays the sender (`scripts/send-test-event.js`),
  and a tunnel such as smee or ngrok for real deliveries, plus the provider's
  redeliver button.
- *What is a replay attack and how do providers prevent it?* Someone captures
  a valid signed request and sends it again later. Idempotency on the id stops
  double processing; some providers (Stripe, Slack) also sign a timestamp and
  reject requests older than a few minutes.

---

## Step 7 - Deploy to AWS Lambda + API Gateway

**Goal.** The same logic as a native Lambda handler (no Express) behind an API
Gateway **HTTP API**, with the secret in an environment variable.

**Concept.** API Gateway receives the HTTPS request and invokes your Lambda
with a JSON *event* describing it (payload format 2.0): `rawPath`,
`requestContext.http.method`, `headers` (lowercased by the HTTP API),
`body` (a string) and `isBase64Encoded`. You return
`{ statusCode, headers, body }`. To verify the signature, rebuild the exact
bytes: `Buffer.from(body, isBase64Encoded ? 'base64' : 'utf8')`.

The big difference: **Lambda freezes the environment as soon as your handler
returns.** Our "enqueue now, process on the next tick" trick from step 3 does
not work there; the background work would not run. So the Lambda version
processes inline and answers `500` on failure (after `store.release(id)`) so
the sender retries. The production shape is: API Gateway -> small Lambda that
verifies, dedupes and puts the event on **SQS** -> worker Lambda that reads
SQS, with a dead-letter queue for poison messages.

**Idempotency in production: DynamoDB.** The in-memory `Set` lives only in one
warm Lambda container; Lambda runs many containers in parallel and recycles
them. Use a DynamoDB table (partition key `eventId`) and claim with a
**conditional put**: `PutItem` with `ConditionExpression:
'attribute_not_exists(eventId)'`. If it fails with
`ConditionalCheckFailedException`, it is a duplicate. Add an `expiresAt`
attribute and enable DynamoDB **TTL** so old ids expire. Same `claim(id)`
interface, so nothing else changes.

**Build.** `starter/src/lambda.js`: `createLambdaHandler(options)` (see the
TODO list in the file) and the exported `handler`, which builds one instance
from `process.env` and caches it in a module variable (built once per cold
start, reused while warm). Do not import Express here.

**Checkpoint.** `npm run test:step7` (calls your handler with fake API Gateway
events; no AWS account needed).

**Deploy (optional, console only).** Cost: Lambda and API Gateway charge per
request; this lab sends a handful. On an account with the AWS Free Tier this
is covered, but Free Tier terms depend on when your account was created, so
check *Billing > Free Tier* first, create a **budget alert** (e.g. US$ 1), and
delete everything at the end.

1. Package the solution (or your starter once green). No `node_modules` needed:
   ```bash
   rm -rf build function.zip && mkdir build && cp -r solution/src build/src
   echo '{"type":"module"}' > build/package.json
   (cd build && zip -r ../function.zip .)
   # no `zip` installed? same result with Python:
   # (cd build && python3 -m zipfile -c ../function.zip src package.json)
   ```
   The zip root must contain `src/` and `package.json` (the `"type": "module"`
   line is what makes Lambda load the `.js` files as ES modules).
2. **Lambda console > Create function**: *Author from scratch*, name
   `webhook-lab`, runtime **Node.js 22.x** (or the newest Node.js offered),
   architecture arm64 or x86_64, default execution role. Create.
3. *Code > Upload from > .zip file*, choose `function.zip`.
   *Runtime settings > Edit*: handler **`src/lambda.handler`**.
4. *Configuration > Environment variables*: `WEBHOOK_SECRET` = a long random
   value (`openssl rand -hex 32`). For real projects keep secrets in Secrets
   Manager or SSM Parameter Store, not plain env vars.
5. *Configuration > General*: timeout 10 s is plenty.
6. **API Gateway console > Create API > HTTP API > Build**: add integration
   *Lambda*, choose `webhook-lab`. Routes: `POST /webhook` and `GET /health`.
   Stage `$default` with auto-deploy. Create, then copy the *Invoke URL*.
7. Test it:
   ```bash
   curl https://<api-id>.execute-api.<region>.amazonaws.com/health
   WEBHOOK_SECRET=<same value> WEBHOOK_URL=https://<api-id>.execute-api.<region>.amazonaws.com/webhook \
     node scripts/send-test-event.js duplicate
   ```
8. Watch the JSON logs in *Lambda > Monitor > View CloudWatch logs*.
9. **Clean up**: delete the HTTP API, the Lambda function, and its CloudWatch
   log group (`/aws/lambda/webhook-lab`).

(Simpler alternative worth knowing: a Lambda **Function URL** gives a public
HTTPS endpoint without API Gateway. API Gateway adds routing, throttling,
custom domains and authorizers.)

Compare with: `solution/src/lambda.js`.

**Explain it out loud.**
- *How did you deploy it?* API Gateway HTTP API in front of a Node.js Lambda.
  The handler rebuilds the raw body (base64 if flagged), verifies the HMAC
  with the secret from configuration, dedupes, processes and returns a status
  code. Logs go to CloudWatch as JSON.
- *Why can't you "respond first, process later" inside Lambda?* The runtime
  freezes after the handler returns, so pending work may never run. For async
  processing put the event on SQS and process it in a second Lambda.
- *How do you make idempotency work across Lambda instances?* A shared store
  with an atomic conditional write: DynamoDB `PutItem` with
  `attribute_not_exists`, plus TTL to expire old ids.

---

## Step 8 - Contact-center flavour: CRM and lead distribution

**Goal.** Turn events into integrations:

| Event | Example `data` | Action |
|---|---|---|
| `call.ended` | `{ callId, contactId, disposition, durationSec, agentId, endedAt }` | append the outcome to the **CRM** contact; `lastDisposition = disposition`; `DO_NOT_CALL` sets `doNotCall: true` |
| `lead.created` | `{ leadId, phone, name, campaign, priority }` | push the lead into the **dialer list** of its campaign (`default` if none), highest priority first |
| anything else | | log `event.ignored`, no error |

Missing required fields (`contactId`/`disposition`, `leadId`/`phone`) throw,
which the queue logs as `event.failed`.

**Concept.** This is where webhooks earn their keep in a contact center. When
a call ends, the platform knows the **disposition** (wrap-up code: sale,
callback, no answer, do not call...). The CRM needs it on the contact so the
next agent, report or campaign sees it. When a lead source (a web form, a
marketplace, a CRM workflow) creates a lead, **lead distribution** means
getting it into the right outbound **contact list** fast, with the right
priority, so the dialer calls while the lead is still warm. A duplicate
`lead.created` would dial the customer twice, so step 4 is not academic here.

The mocks (`crm.js`, `dialer.js`) stand in for real APIs: a Salesforce or
HubSpot REST call that updates a Contact, and a Genesys Cloud contact list or
NICE CXone calling list that an outbound campaign dials. In real life each
mock method becomes an authenticated HTTP call with its own timeouts and
retries, which is exactly why it runs in the background worker and not in the
request.

**Why this step exists.** This lab was built to prepare for integration
roles such as the Howdy-placed position focused on **CRM and lead-distribution
integration**: receive events from one system, verify them, and reliably
update a CRM record or route a lead to a dialer. Steps 1-7 are the plumbing;
step 8 is the business logic that plumbing protects.

**Build.** `starter/src/handlers.js`: `createEventHandler({ crm, dialer, logger })`
with a route table `{ 'call.ended': fn, 'lead.created': fn }`. Then in
`app.js`, default `handleEvent` to it:

```js
const {
  crm = createMockCrm(),
  dialer = createMockDialer(),
  handleEvent = createEventHandler({ crm, dialer, logger }),
} = options;
```

**Checkpoint.** `npm run test:step8`, then `npm test`: all green. By hand:

```bash
node scripts/send-test-event.js call-ended
node scripts/send-test-event.js lead-created
```

Compare with: `solution/src/handlers.js`.

**Explain it out loud.**
- *Walk me through what happens when a call ends.* The platform POSTs
  `call.ended` with a signature. I verify the HMAC on the raw body, validate,
  dedupe on the event id, enqueue and answer 200 in milliseconds. The worker
  maps the disposition onto the CRM contact through the CRM's REST API;
  failures are logged with the event id and retried from a dead-letter path.
- *How would you design lead distribution with webhooks?* `lead.created`
  arrives, I dedupe it (never dial twice), validate the phone, check do-not-call,
  pick the list by campaign and priority, and push it to the dialer's contact
  list API. Fast acknowledgement, durable queue, idempotent writes.
- *What if the CRM is down?* The webhook was already acknowledged, so the
  sender will not retry. The worker retries with backoff, then parks the event
  in a dead-letter queue and alerts; idempotency makes a later re-processing safe.

---

## Command reference

| Command | What it does |
|---|---|
| `npm install` | install Express (runtime) and supertest (tests) |
| `npm start` | run **your** server (`starter/`), needs `WEBHOOK_SECRET` |
| `npm run start:solution` | run the reference server |
| `npm run test:stepN` | run one step's tests against `starter/` |
| `npm test` | all steps against `starter/` |
| `npm run test:solution` | all steps against `solution/` |
| `node scripts/send-test-event.js <mode>` | `valid`, `bad-signature`, `no-signature`, `invalid-json`, `duplicate`, `call-ended`, `lead-created` |

Environment: `WEBHOOK_SECRET` (required), `PORT` (3000), `WEBHOOK_SOURCE`
(`generic` or `github`), `LOG_LEVEL` (`info`), `WEBHOOK_URL` (sender target).

## The 30-second answer

> "A webhook receiver is a public HTTP endpoint, so first I authenticate:
> HMAC-SHA256 of the raw body with a shared secret, compared in constant time.
> Then I validate and normalize the payload, dedupe on the event id because
> delivery is at-least-once, put it on a queue and return 2xx within
> milliseconds so the sender doesn't time out and retry. A worker does the
> slow part, like updating the CRM or pushing a lead to the dialer list, with
> structured logs, retries and a dead-letter queue. On AWS that's API Gateway,
> Lambda, SQS and DynamoDB for the idempotency keys."
