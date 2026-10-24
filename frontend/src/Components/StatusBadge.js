import React from 'react';

const TONE = {
  PendingPayment: 'text-bg-warning',
  PendingAcceptance: 'text-bg-info',
  PendingPreparation: 'text-bg-primary',
  PendingCollection: 'text-bg-success',
  Collected: 'text-bg-secondary',
  Rejected: 'text-bg-danger',
  Refunded: 'text-bg-dark',
  NoShow: 'text-bg-dark',
};

// The stored status is the system's word; these are the persona's.
const WORDS = {
  PendingPayment: 'Awaiting payment',
  PendingAcceptance: 'Waiting for the stall',
  PendingPreparation: 'Being prepared',
  PendingCollection: 'Ready to collect',
  Collected: 'Collected',
  Rejected: 'Rejected',
  Refunded: 'Refunded',
  NoShow: 'Not collected',
};

export function StatusBadge({ status }) {
  return (
    <span className={`badge ${TONE[status] || 'text-bg-secondary'}`}>
      {WORDS[status] || status}
    </span>
  );
}