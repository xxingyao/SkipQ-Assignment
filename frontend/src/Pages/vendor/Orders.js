import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { vendorApi } from '../../api/endpoints';
import { useRequest } from '../../api/useRequest';
import { Notice } from '../../Components/Notice';
import { StatusBadge } from '../../Components/StatusBadge';
import { actionsFor } from '../../domain/orderActions';

// The GBA mockups group the vendor's board by stage rather than listing every
// order together, because what a stall owner needs at a glance is how much is
// waiting against how much is cooking.
const COLUMNS = [
  { title: 'Pending', statuses: ['PendingPayment', 'PendingAcceptance'] },
  { title: 'Preparing', statuses: ['PendingPreparation'] },
  { title: 'Ready', statuses: ['PendingCollection'] },
  { title: 'Completed', statuses: ['Collected', 'Rejected', 'Refunded', 'NoShow'] },
];

export function Orders() {
  const { credentials } = useAuth();
  const { run: load, error: loadError } = useRequest();
  const { run: move, pending: moving, error: moveError } = useRequest();
  const [orders, setOrders] = useState([]);

  const refresh = useCallback(() => {
    load(() => vendorApi.orders(credentials)).then((d) => { if (d) setOrders(d.orders); });
  }, [load, credentials]);

  useEffect(() => { refresh(); }, [refresh]);

  async function advance(order, action) {
    let reason;
    if (action.needsReason) {
      reason = window.prompt('Why are you rejecting this order? The diner will see this.');
      if (!reason) return;           // a rejection with no reason is never sent
    }
    const updated = await move(() =>
      vendorApi.advance(credentials, order.id, action.status, reason));
    if (updated) refresh();
  }

  return (
    <>
      <Notice error={loadError || moveError} />
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="h5 mb-0">Orders</h2>
        <button className="btn btn-outline-secondary btn-sm" onClick={refresh}>Refresh</button>
      </div>

      <div className="row g-3">
        {COLUMNS.map((column) => {
          const inColumn = orders.filter((o) => column.statuses.includes(o.status));
          return (
            <div className="col-md-3" key={column.title}>
              <h3 className="h6 text-muted">
                {column.title}{' '}
                <span className="badge text-bg-light">{inColumn.length}</span>
              </h3>

              {inColumn.length === 0 && <p className="small text-muted">Nothing here.</p>}

              {inColumn.map((order) => (
                <div className="card mb-2" key={order.id}>
                  <div className="card-body p-2">
                    <div className="d-flex justify-content-between align-items-start mb-1">
                      <span className="fw-semibold small">
                        {order.queue_number ? `#${order.queue_number}` : 'Unpaid'}
                      </span>
                      <StatusBadge status={order.status} />
                    </div>
                    <div className="small text-muted">{order.diner_name}</div>

                    <ul className="list-unstyled small mb-1 mt-1">
                      {order.items.map((line, index) => (
                        <li key={index}>{line.quantity} × {line.name}</li>
                      ))}
                    </ul>
                    <div className="small fw-semibold mb-2">${order.total.toFixed(2)}</div>

                    {order.rejection_reason && (
                      <p className="small text-danger mb-2">{order.rejection_reason}</p>
                    )}

                    {/* Only moves the guard permits from this state are rendered. */}
                    <div className="d-grid gap-1">
                      {actionsFor(order).map((action) => (
                        <button key={action.status}
                                className={`btn btn-${action.variant} btn-sm`}
                                onClick={() => advance(order, action)}
                                disabled={moving}>
                          {action.label}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          );
        })}
      </div>
    </>
  );
}