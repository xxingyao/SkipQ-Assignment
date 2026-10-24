import React from 'react';
import { Stalls } from './Stalls';
import { StallMenu } from './StallMenu';
import { MyOrders } from './MyOrders';
import { Link, Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';
import { OrderDetail } from './OrderDetail';

export function DinerShell() {
  const { session, signOut } = useAuth();
  return (
    <div className="container py-4">
      <header className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h1 className="h4 mb-0">SkipQ</h1>
          <small className="text-muted">Signed in as {session.name} — diner</small>
        </div>
        <button className="btn btn-outline-secondary btn-sm" onClick={signOut}>Sign out</button>
      </header>
      <nav className="mb-3">
        <Link className="btn btn-link ps-0" to="/diner/stalls">Stalls</Link>
        <Link className="btn btn-link" to="/diner/orders">My orders</Link>
      </nav>
      <Routes>
        <Route index element={<Navigate to="stalls" replace />} />
        <Route path="stalls" element={<Stalls />} />
        <Route path="stalls/:stallId" element={<StallMenu />} />
        <Route path="orders" element={<MyOrders />} />
        <Route path="orders/:orderId" element={<OrderDetail />} />
      </Routes>
    </div>
  );
}