// Step 8 - a mock outbound dialer. Stands in for a Genesys Cloud contact list
// or a NICE CXone calling list that an outbound campaign dials from.

export function createMockDialer() {
  const lists = new Map();
  return {
    lists,
    /** Contacts in a list, highest priority first. */
    list(name) {
      return [...(lists.get(name) ?? [])].sort((a, b) => b.priority - a.priority);
    },
    async enqueueLead(listName, lead) {
      if (!lists.has(listName)) lists.set(listName, []);
      lists.get(listName).push(lead);
      return lead;
    },
  };
}
