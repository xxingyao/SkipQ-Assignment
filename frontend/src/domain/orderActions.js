// Which buttons a vendor is offered for an order. The backend owns the rule;
// this mirrors only the question of what to show, so no control is ever offered
// for a move the guard would refuse. The backend still refuses if this is wrong.
export const NO_SHOW_AFTER_MINUTES = 30;

function readySince(order) {
  // The API sends naive UTC, so it is read as UTC rather than local time.
  return new Date(`${order.status_updated_at}Z`).getTime();
}

export function readyLongEnoughForNoShow(order) {
  return Date.now() - readySince(order) >= NO_SHOW_AFTER_MINUTES * 60 * 1000;
}

export function actionsFor(order) {
  switch (order.status) {
    case 'PendingAcceptance':
      return [
        { label: 'Accept', status: 'PendingPreparation', variant: 'primary' },
        { label: 'Reject', status: 'Rejected', variant: 'outline-danger', needsReason: true },
      ];
    case 'PendingPreparation':
      return [
        { label: 'Ready for collection', status: 'PendingCollection', variant: 'primary' },
        { label: 'Refund', status: 'Refunded', variant: 'outline-secondary' },
      ];
    case 'PendingCollection':
      return [
        { label: 'Collected', status: 'Collected', variant: 'primary' },
        ...(readyLongEnoughForNoShow(order)
          ? [{ label: 'No-show', status: 'NoShow', variant: 'outline-secondary' }]
          : []),
      ];
    case 'Rejected':
      return [{ label: 'Refund', status: 'Refunded', variant: 'outline-secondary' }];
    default:
      return [];   // Collected, Refunded and NoShow are terminal
  }
}