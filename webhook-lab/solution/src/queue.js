// Step 3 - a tiny in-memory work queue.
//
// The HTTP handler only enqueues; a worker drains the queue in the
// background. This lets us answer the sender in milliseconds.
//
// Limitation (say it in the interview): it lives in process memory. If the
// process crashes or restarts, queued events are lost. In production you
// would use a durable queue (SQS, RabbitMQ, a database table...).

export function createQueue({ worker, concurrency = 1, onError = () => {} }) {
  const pending = [];
  let running = 0;
  let idleWaiters = [];

  function pump() {
    while (running < concurrency && pending.length > 0) {
      const job = pending.shift();
      running += 1;
      Promise.resolve()
        .then(() => worker(job))
        .catch((err) => onError(err, job))
        .finally(() => {
          running -= 1;
          pump();
        });
    }
    if (running === 0 && pending.length === 0) {
      const waiters = idleWaiters;
      idleWaiters = [];
      waiters.forEach((resolve) => resolve());
    }
  }

  return {
    enqueue(job) {
      pending.push(job);
      // Start on the next tick, after the HTTP response has been sent.
      setImmediate(pump);
    },
    /** Resolves when nothing is pending or running (handy in tests and on shutdown). */
    onIdle() {
      if (running === 0 && pending.length === 0) return Promise.resolve();
      return new Promise((resolve) => idleWaiters.push(resolve));
    },
    get depth() {
      return pending.length + running;
    },
  };
}
