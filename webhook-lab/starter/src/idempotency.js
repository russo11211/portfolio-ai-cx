// Step 4 - idempotency store.
// README: "Step 4". Run: npm run test:step4
//
// createMemoryStore() must return an object with ASYNC methods:
//   claim(id)   - true the first time an id is seen, false afterwards
//                 (check-and-remember as ONE operation)
//   release(id) - forget an id so it can be claimed again
// Hint: a Set is enough.
export function createMemoryStore() {
  throw new Error('TODO(step 4): implement createMemoryStore');
}
