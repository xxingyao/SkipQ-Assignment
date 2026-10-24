import React from 'react';

// One place decides how a refusal looks. 4xx is the persona's to act on;
// anything else is a fault they cannot fix.
export function Notice({ error, success }) {
  if (!error && !success) return null;
  if (error) {
    const actionable = error.status >= 400 && error.status < 500;
    return (
      <div className={`alert ${actionable ? 'alert-warning' : 'alert-danger'}`} role="alert">
        {error.message}
      </div>
    );
  }
  return <div className="alert alert-success" role="status">{success}</div>;
}