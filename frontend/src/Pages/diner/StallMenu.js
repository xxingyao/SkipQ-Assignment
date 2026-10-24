import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { dinerApi } from '../../api/endpoints';
import { useRequest } from '../../api/useRequest';
import { Notice } from '../../Components/Notice';

export function StallMenu() {
  const { stallId } = useParams();
  const { credentials } = useAuth();
  const navigate = useNavigate();

  const { run: load, pending: loading, error: loadError } = useRequest();
  const { run: submit, pending: placing, error: placeError } = useRequest();

  const [stall, setStall] = useState(null);
  const [items, setItems] = useState([]);
  const [cart, setCart] = useState({});   // item id -> quantity, browser-side only

  useEffect(() => {
    load(() => dinerApi.menu(credentials, stallId)).then((data) => {
      if (data) { setStall(data.stall); setItems(data.items); }
    });
  }, [load, credentials, stallId]);

  function change(itemId, delta) {
    setCart((current) => {
      const next = { ...current };
      const quantity = (next[itemId] || 0) + delta;
      if (quantity <= 0) delete next[itemId]; else next[itemId] = Math.min(quantity, 20);
      return next;
    });
  }

  const lines = Object.entries(cart).map(([item_id, quantity]) => ({ item_id, quantity }));
  const total = lines.reduce((sum, line) => {
    const item = items.find((i) => i.id === line.item_id);
    return sum + (item ? item.price * line.quantity : 0);
  }, 0);

  async function placeOrder() {
    const order = await submit(() => dinerApi.placeOrder(credentials, stallId, lines));
    if (order) navigate('/diner/orders');
  }

  if (loading && !stall) return <p className="text-muted">Loading menu…</p>;

  return (
    <>
      <Notice error={loadError || placeError} />
      {stall && (
        <h2 className="h5 mb-3">
          {stall.stall_name}{' '}
          {!stall.is_accepting_orders && <span className="badge text-bg-secondary">Closed</span>}
        </h2>
      )}

      <ul className="list-group mb-4">
        {items.map((item) => (
          <li className="list-group-item d-flex justify-content-between align-items-center"
              key={item.id}>
            <div>
              <div className="fw-semibold">
                {item.name}{' '}
                {/* Sold out is visible before the diner tries to order it. */}
                {!item.orderable && <span className="badge text-bg-secondary ms-1">Sold out</span>}
              </div>
              <div className="text-muted small">{item.description}</div>
              <div className="small">${item.price.toFixed(2)}</div>
            </div>
            <div className="d-flex align-items-center gap-2">
              <button className="btn btn-outline-secondary btn-sm"
                      onClick={() => change(item.id, -1)}
                      disabled={!item.orderable || !cart[item.id]}>−</button>
              <span style={{ minWidth: '1.5rem', textAlign: 'center' }}>
                {cart[item.id] || 0}
              </span>
              <button className="btn btn-outline-secondary btn-sm"
                      onClick={() => change(item.id, 1)}
                      disabled={!item.orderable}>+</button>
            </div>
          </li>
        ))}
      </ul>

      <div className="d-flex justify-content-between align-items-center">
        <strong>Total ${total.toFixed(2)}</strong>
        {/* placing is true while the request is in flight, so a second click
            cannot create a second order. */}
        <button className="btn btn-primary"
                onClick={placeOrder}
                disabled={lines.length === 0 || placing}>
          {placing ? 'Placing…' : 'Place order'}
        </button>
      </div>
    </>
  );
}