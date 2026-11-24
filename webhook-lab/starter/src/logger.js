// Step 5 - structured (JSON) logging.
// README: "Step 5". Run: npm run test:step5
//
// createLogger({ level = 'info', write = line => process.stdout.write(line + '\n'), base = {} })
// returns { debug, info, warn, error }, each (msg, fields = {}) => void.
// Each call writes ONE line: JSON.stringify({ time, level, msg, ...base, ...fields })
// and skips levels below `level` (debug < info < warn < error).
export function createLogger(options = {}) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 5): implement createLogger');
}
