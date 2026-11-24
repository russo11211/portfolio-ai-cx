// Step 5 - structured (JSON) logging.
//
// One JSON object per line. Machines (CloudWatch, Datadog, Loki...) can
// filter and aggregate by field: level, msg, eventId, type...
// Never log secrets, signatures or full payloads (they can contain PII).

const LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

export function createLogger({
  level = 'info',
  write = (line) => process.stdout.write(line + '\n'),
  base = {},
} = {}) {
  const min = LEVELS[level] ?? LEVELS.info;
  const make = (lvl) => (msg, fields = {}) => {
    if (LEVELS[lvl] < min) return;
    write(JSON.stringify({ time: new Date().toISOString(), level: lvl, msg, ...base, ...fields }));
  };
  return { debug: make('debug'), info: make('info'), warn: make('warn'), error: make('error') };
}
