import { actionsFor, NO_SHOW_AFTER_MINUTES } from './orderActions';

// actionsFor() expects naive UTC timestamps, as the API sends them.
const minutesAgo = (n) =>
  new Date(Date.now() - n * 60 * 1000).toISOString().replace('Z', '');

describe('actionsFor', () => {
  test('a new order can be accepted or rejected', () => {
    const labels = actionsFor({ status: 'PendingAcceptance' }).map((a) => a.label);
    expect(labels).toEqual(['Accept', 'Reject']);
  });

  test('terminal orders offer no actions', () => {
    ['Collected', 'Refunded', 'NoShow'].forEach((status) => {
      expect(actionsFor({ status })).toEqual([]);
    });
  });

  test('no-show is only offered after the waiting time', () => {
    const late = { status: 'PendingCollection', status_updated_at: minutesAgo(NO_SHOW_AFTER_MINUTES + 1) };
    const fresh = { status: 'PendingCollection', status_updated_at: minutesAgo(0) };
    expect(actionsFor(late).map((a) => a.label)).toContain('No-show');
    expect(actionsFor(fresh).map((a) => a.label)).not.toContain('No-show');
  });

  // Was deliberately failing in Q4a; fixed in Q4c (red -> green).
  test('a rejected order can be refunded', () => {
    expect(actionsFor({ status: 'Rejected' })[0].label).toBe('Refund');
  });
});