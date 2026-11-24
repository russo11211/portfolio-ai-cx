// Step 8 - business logic: route each event type to the right integration.
//
//   call.ended   -> write the call disposition onto the CRM contact
//   lead.created -> push the lead into the dialer list of its campaign
//
// Anything else is logged and ignored (never an error: senders often add
// new event types, and a 4xx/5xx would make them retry forever).

export function createEventHandler({ crm, dialer, logger }) {
  const routes = {
    async 'call.ended'(event) {
      const { callId, contactId, disposition, durationSec, agentId, endedAt } = event.data;
      if (!contactId || !disposition) {
        throw new Error('call.ended requires data.contactId and data.disposition');
      }
      await crm.logCallOutcome(contactId, {
        eventId: event.id,
        callId,
        disposition,
        durationSec,
        agentId,
        endedAt,
      });
    },

    async 'lead.created'(event) {
      const { leadId, phone, name, campaign, priority } = event.data;
      if (!leadId || !phone) {
        throw new Error('lead.created requires data.leadId and data.phone');
      }
      await dialer.enqueueLead(campaign ?? 'default', {
        leadId,
        phone,
        name,
        priority: priority ?? 0,
      });
    },
  };

  return async function handleEvent(event) {
    const route = routes[event.type];
    if (!route) {
      logger.info('event.ignored', { eventId: event.id, type: event.type });
      return;
    }
    await route(event);
    logger.info('event.processed', { eventId: event.id, type: event.type });
  };
}
