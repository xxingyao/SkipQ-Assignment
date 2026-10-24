import { useCallback, useRef, useState } from 'react';
import { ApiError } from './client';

// Owns three things every screen would otherwise repeat: whether a request is
// in flight, the refusal if one came back, and the guarantee that a second
// submit while the first is still running does nothing.
export function useRequest() {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState(null);
  const inFlight = useRef(false);

  const run = useCallback(async (work) => {
    if (inFlight.current) return undefined;
    inFlight.current = true;
    setPending(true);
    setError(null);
    try {
      return await work();
    } catch (failure) {
      setError(failure instanceof ApiError
        ? failure
        : new ApiError(0, failure.message || 'Something went wrong'));
      return undefined;
    } finally {
      inFlight.current = false;
      setPending(false);
    }
  }, []);

  return { run, pending, error, clearError: () => setError(null) };
}