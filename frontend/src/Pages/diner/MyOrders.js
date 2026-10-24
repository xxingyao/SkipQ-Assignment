import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { dinerApi } from '../../api/endpoints';
import { useRequest } from '../../api/useRequest';
import { Notice } from '../../Components/Notice';
import { StatusBadge } from '../../Components/StatusBadge';

export function MyOrders() {
  const { credentials } = useAuth();

  // Each independent request gets its own hook: the in-flight guard exists to
  // stop one action being submitted twice, not to stop two different reads.
  const { run: loadOrders, error: ordersError } = useRequest();
  const { run: loadNotifications, error: notificationsError } = useRequest();
  const { run: dismiss, pending: dismissing } = useRequest();
  const { run: pay, pending: paying, error: payError } = useRequest();

  const [orders, setOrders] = useState([]);
  const [notifications, setNotifications] = useState([]);

  const refresh = useCallback(() => {
    loadOrders(() => dinerApi.orders(credentials))
      .then((d) => { if (d) setOrders(d.orders); });
    loadNotifications(() => dinerApi.notifications(credentials))
      .then((d) => { if (d) setNotifications(d.notifications); });
  }, [loadOrders, loadNotifications, credentials]);

  useEffect(() => { refresh(); }, [refresh]);

  // Clearing them on the server is what stops the banner growing without end;
  // clearing them here as well just saves a round trip.
  async function dismissAll() {
    const done = await dismiss(() => dinerApi.dismissNotifications(credentials));
    if (done) setNotifications([]);
  }

  async function payFor(orderId) {
    const updated = await pay(() => dinerApi.pay(credentials, orderId, 'PayNow'));
    if (updated) refresh();
  }

  return (
    <>
      <Notice error={ordersError || notificationsError || payError} />

      {notifications.length > 0 && (
        <div className="alert alert-info">
          <div className="d-flex justify-content-between align-items-start">
            <div>
              {notifications.map((n) => <div key={n.id}>{n.message}</div>)}
            </div>
            <button className="btn btn-outline-secondary btn-sm ms-3"
                    onClick={dismissAll} disabled={dismissing}>
              {dismissing ? 'Dismissing…' : 'Dismiss'}
            </button>
          </div>
        </div>
      )}

      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="h5 mb-0">My orders</h2>
        <button className="btn btn-outline-secondary btn-sm" onClick={refresh}>Refresh</button>
      </div>

      {orders.length === 0 && <p className="text-muted">No orders yet.</p>}

      {orders.map((order) => (
        <div className="card mb-2" key={order.id}>
          <div className="card-body">
            <div className="d-flex justify-content-between align-items-start">
              <div>
                <Link className="fw-semibold" to={`/diner/orders/${order.id}`}>
                  {order.stall_name}
                </Link>
                <div className="text-muted small">
                  {order.queue_number ? `Queue ${order.queue_number}` : 'No queue number yet'}
                </div>
              </div>
              <StatusBadge status={order.status} />
            </div>

            <ul className="list-unstyled small mt-2 mb-2">
              {order.items.map((line, index) => (
                <li key={index}>{line.quantity} × {line.name} — ${line.subtotal.toFixed(2)}</li>
              ))}
            </ul>

            {order.rejection_reason && (
              <p className="small text-danger mb-2">Reason: {order.rejection_reason}</p>
            )}

            <div className="d-flex justify-content-between align-items-center">
              <strong>${order.total.toFixed(2)}</strong>
              {/* Pay is offered only in the one state that permits it. */}
              {order.status === 'PendingPayment' && (
                <button className="btn btn-primary btn-sm"
                        onClick={() => payFor(order.id)} disabled={paying}>
                  {paying ? 'Paying…' : 'Pay with PayNow'}
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </>
  );
}