import React from 'react';
import { Orders } from './Orders';
import { Menu } from './Menu';
import { Dashboard } from './Dashboard';
import { Link, Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from '../../auth/AuthContext';

export function VendorShell() {
  const { session, signOut } = useAuth();
  return (
    <div className="container py-4">
      <header className="d-flex justify-content-between align-items-center mb-3">
        <div>
          <h1 className="h4 mb-0">SkipQ</h1>
          <small className="text-muted">Signed in as {session.name} — stall owner</small>
        </div>
        <button className="btn btn-outline-secondary btn-sm" onClick={signOut}>Sign out</button>
      </header>
      <nav className="mb-3">
        <Link className="btn btn-link ps-0" to="/vendor/orders">Orders</Link>
        <Link className="btn btn-link" to="/vendor/menu">Menu</Link>
        <Link className="btn btn-link" to="/vendor/dashboard">Dashboard</Link>
      </nav>
      <Routes>
        <Route index element={<Navigate to="orders" replace />} />
        <Route path="orders" element={<Orders />} />
        <Route path="menu" element={<Menu />} />
        <Route path="dashboard" element={<Dashboard />} />
      </Routes>
    </div>
  );
}