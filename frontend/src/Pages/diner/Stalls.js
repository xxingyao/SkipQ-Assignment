import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { dinerApi } from '../../api/endpoints';
import { useRequest } from '../../api/useRequest';
import { Notice } from '../../Components/Notice';

export function Stalls() {
  const { credentials } = useAuth();
  const { run, pending, error } = useRequest();
  const [stalls, setStalls] = useState([]);

  useEffect(() => {
    run(() => dinerApi.stalls(credentials)).then((data) => {
      if (data) setStalls(data.stalls);
    });
  }, [run, credentials]);

  if (pending && stalls.length === 0) return <p className="text-muted">Loading stalls…</p>;

  return (
    <>
      <Notice error={error} />
      <div className="row g-3">
        {stalls.map((stall) => (
          <div className="col-md-6" key={stall.id}>
            <div className="card h-100">
              <div className="card-body">
                <div className="d-flex justify-content-between align-items-start">
                  <h2 className="h5 mb-1">{stall.stall_name}</h2>
                  {stall.is_accepting_orders
                    ? <span className="badge text-bg-success">Open</span>
                    : <span className="badge text-bg-secondary">Closed</span>}
                </div>
                <p className="text-muted small mb-3">{stall.venue_type}</p>
                {/* A closed stall is shown as closed before the diner acts, and
                    is offered no control that would be refused. */}
                {stall.is_accepting_orders ? (
                  <Link className="btn btn-primary btn-sm" to={`/diner/stalls/${stall.id}`}>
                    View menu
                  </Link>
                ) : (
                  <button className="btn btn-primary btn-sm" disabled>
                    Not taking orders
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}