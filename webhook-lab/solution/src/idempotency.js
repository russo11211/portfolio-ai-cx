// Step 4 - idempotency store.
//
// Senders deliver "at least once": the same event can arrive twice (a retry
// after a timeout, a manual redelivery...). We remember which event ids we
// have already accepted and skip the duplicates.
//
// The interface is async on purpose, so it can be swapped for a real
// database (SQLite, Redis, DynamoDB) without changing the callers.

export function createMemoryStore() {
  const seen = new Set();
  return {
    /**
     * Atomically "check and remember". Returns true the first time an id is
     * claimed, false for every later attempt. Check-then-set must be ONE
     * operation, otherwise two concurrent deliveries could both pass the check.
     */
    async claim(id) {
      if (seen.has(id)) return false;
      seen.add(id);
      return true;
    },
    /** Forget an id, so a retry of a failed event can be processed again. */
    async release(id) {
      seen.delete(id);
    },
    get size() {
      return seen.size;
    },
  };
}
