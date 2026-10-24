import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';
import { authApi } from '../api/endpoints';

const AuthContext = createContext(null);
const STORAGE_KEY = 'skipq.session';

function readStoredSession() {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch (unavailable) {
    return null;   // private windows and blocked storage must not break sign-in
  }
}

export function AuthProvider({ children }) {
  const [session, setSession] = useState(readStoredSession);

  const signIn = useCallback(async (email, password) => {
    const { token, role, name } = await authApi.getToken(email, password);
    const next = { email, token, role, name };
    setSession(next);
    try {
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch (unavailable) { /* a refresh will simply ask again */ }
    return next;
  }, []);

  const signOut = useCallback(() => {
    setSession(null);
    try { window.sessionStorage.removeItem(STORAGE_KEY); } catch (unavailable) {}
  }, []);

  const value = useMemo(() => ({
    session,
    credentials: session ? { email: session.email, token: session.token } : null,
    role: session ? session.role : null,
    signIn,
    signOut,
  }), [session, signIn, signOut]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error('useAuth must be used inside an AuthProvider');
  return value;
}