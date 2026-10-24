import React, { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { dinerApi } from '../../api/endpoints';
import { useRequest } from '../../api/useRequest';
import { Notice } from '../../Components/Notice';
import { StatusBadge } from '../../Components/StatusBadge';

export function OrderDetail() {
  const { orderId } = useParams();
  const { credentials } = useAuth();
  const { run, error } = useRequest();
  const [order, setOrder] = useState(null);

  const refresh = useCallback(() => {
    run(() => dinerApi.order(credentials, orderId)).then((d) => { if (d) setOrder(d); });
  }, [run, credentials, orderId]);

  useEffect(() => { refresh(); }, [refresh]);

  if (!order) return <><Notice error={error} /><p className="text-muted">Loading…</p></>;

  return (
    <>
      <Notice error={error} />
      <Link className="btn btn-link ps-0 mb-2" to="/diner/orders">← All orders</Link>

      <div className="card">
        <div className="card-body">
          <div className="d-flex justify-content-between align-items-start mb-3">
            <div>
              <h2 className="h5 mb-0">{order.stall_name}</h2>
              <small className="text-muted">
                Placed {new Date(order.created_at + 'Z').toLocaleString()}
              </small>            </div>
            <StatusBadge status={order.status} />
          </div>

          <div className="display-6 mb-3">
            {order.queue_number
              ? `Queue ${order.queue_number}`
              : <span className="h6 text-muted">No queue number until the order is paid</span>}
          </div>

          <ul className="list-unstyled small">
            {order.items.map((line, index) => (
              <li key={index}>
                {line.quantity} × {line.name} — ${line.subtotal.toFixed(2)}
              </li>
            ))}
          </ul>

          {order.rejection_reason && (
            <p className="text-danger small">Reason: {order.rejection_reason}</p>
          )}

          <div className="d-flex justify-content-between align-items-center mt-3">
            <strong>${order.total.toFixed(2)}</strong>
            <button className="btn btn-outline-secondary btn-sm" onClick={refresh}>
              Refresh status
            </button>
          </div>
        </div>
      </div>
    </>
  );
}