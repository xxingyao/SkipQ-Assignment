import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import { useRequest } from '../api/useRequest';
import { Notice } from '../Components/Notice';

export function SignIn() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { signIn } = useAuth();
  const { run, pending, error } = useRequest();
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    const session = await run(() => signIn(email.trim(), password));
    if (session) navigate(session.role === 'Vendor' ? '/vendor' : '/diner');
  }

  return (
    <div className="container" style={{ maxWidth: 420, marginTop: '4rem' }}>
      <h1 className="h3">Log In</h1>
      <p className="text-muted">Sign in as a diner or a stall owner.</p>
      <Notice error={error} />
      <form onSubmit={handleSubmit}>
        <div className="mb-3">
          <label className="form-label" htmlFor="email">Email</label>
          <input id="email" className="form-control" type="email" required
                 value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div className="mb-3">
          <label className="form-label" htmlFor="password">Password</label>
          <input id="password" className="form-control" type="password" required
                 value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>
        <button className="btn btn-primary w-100" type="submit" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
    </div>
  );
}