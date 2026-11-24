// Step 8 - a mock CRM. Stands in for Salesforce / HubSpot / a client's CRM API.
// In real life each method would be an authenticated REST call.

export function createMockCrm() {
  const records = new Map();

  function getOrCreate(contactId) {
    if (!records.has(contactId)) {
      records.set(contactId, { contactId, callHistory: [], lastDisposition: null, doNotCall: false });
    }
    return records.get(contactId);
  }

  return {
    records,
    get(contactId) {
      return records.get(contactId);
    },
    /** Writes the outcome of a finished call onto the contact record. */
    async logCallOutcome(contactId, outcome) {
      const record = getOrCreate(contactId);
      record.callHistory.push(outcome);
      record.lastDisposition = outcome.disposition;
      if (outcome.disposition === 'DO_NOT_CALL') {
        record.doNotCall = true;
      }
      return record;
    },
  };
}
