import React, { useCallback, useEffect, useState } from 'react';
import { useAuth } from '../../auth/AuthContext';
import { vendorApi } from '../../api/endpoints';
import { useRequest } from '../../api/useRequest';
import { Notice } from '../../Components/Notice';

export function Dashboard() {
  const { credentials } = useAuth();
  const { run, error } = useRequest();
  const [board, setBoard] = useState(null);

  const refresh = useCallback(() => {
    run(() => vendorApi.dashboard(credentials)).then((d) => { if (d) setBoard(d); });
  }, [run, credentials]);

  useEffect(() => { refresh(); }, [refresh]);

  if (!board) return <><Notice error={error} /><p className="text-muted">Loading…</p></>;

  return (
    <>
      <Notice error={error} />
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h2 className="h5 mb-0">Today — {board.sales.date}</h2>
        <button className="btn btn-outline-secondary btn-sm" onClick={refresh}>Refresh</button>
      </div>

      <div className="row g-3 mb-4">
        <div className="col-sm-6">
          <div className="card"><div className="card-body">
            <div className="text-muted small">Takings</div>
            <div className="h4 mb-0">${board.sales.total_takings.toFixed(2)}</div>
          </div></div>
        </div>
        <div className="col-sm-6">
          <div className="card"><div className="card-body">
            <div className="text-muted small">Orders</div>
            <div className="h4 mb-0">{board.sales.order_count}</div>
          </div></div>
        </div>
      </div>

      <h3 className="h6">Top items</h3>
      {board.top_items.length === 0
        ? <p className="text-muted small">Nothing sold yet today.</p>
        : <ol className="small">
            {board.top_items.map((entry) => (
              <li key={entry.name}>{entry.name} — {entry.quantity}</li>
            ))}
          </ol>}

      <h3 className="h6 mt-3">Sold out</h3>
      {board.sold_out.length === 0
        ? <p className="text-muted small">Everything is in stock.</p>
        : <ul className="small">
            {board.sold_out.map((item) => <li key={item.id}>{item.name}</li>)}
          </ul>}
    </>
  );
}