import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

// Gating happens here, once, at the route. A persona who is signed out is sent
// to sign in; one with the wrong role is sent to their own area rather than
// shown a screen they cannot use.
export function RequireRole({ role, children }) {
  const { session } = useAuth();
  const location = useLocation();

  if (!session) return <Navigate to="/" replace state={{ from: location }} />;
  if (session.role !== role) {
    return <Navigate to={session.role === 'Vendor' ? '/vendor' : '/diner'} replace />;
  }
  return children;
}