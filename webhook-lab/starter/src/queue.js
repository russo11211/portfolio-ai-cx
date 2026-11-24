// Step 3 - a tiny in-memory work queue.
// README: "Step 3". Run: npm run test:step3
//
// createQueue({ worker, concurrency = 1, onError }) must return:
//   enqueue(job)  - add a job; start working on the next tick (setImmediate)
//   onIdle()      - a Promise that resolves when nothing is pending or running
//   depth         - getter: pending + running jobs
// A job whose worker throws/rejects calls onError(err, job) and the queue keeps going.
export function createQueue({ worker, concurrency = 1, onError = () => {} }) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 3): implement createQueue');
}
