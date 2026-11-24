// Step 8 - route contact-center events to the CRM and the dialer.
// README: "Step 8". Run: npm run test:step8
//
// createEventHandler({ crm, dialer, logger }) returns async handleEvent(event):
//   'call.ended'   -> crm.logCallOutcome(data.contactId, { eventId, callId, disposition,
//                     durationSec, agentId, endedAt }); throw if contactId/disposition missing
//   'lead.created' -> dialer.enqueueLead(data.campaign ?? 'default', { leadId, phone, name,
//                     priority: priority ?? 0 }); throw if leadId/phone missing
//   anything else  -> logger.info('event.ignored', { eventId, type }) and return (no error)
// The mocks in crm.js and dialer.js are already written for you.
export function createEventHandler({ crm, dialer, logger }) { // eslint-disable-line no-unused-vars
  throw new Error('TODO(step 8): implement createEventHandler');
}
