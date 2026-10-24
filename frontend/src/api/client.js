// Every request to SkipQ goes through here. The base URL is resolved once from
// the environment, and the token is attached once, so no page rebuilds either.
const BASE_URL = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5000';

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

function authHeader(credentials) {
  if (!credentials) return {};
  return { Authorization: 'Basic ' + btoa(`${credentials.email}:${credentials.token}`) };
}

export async function request(path, { method = 'GET', body, credentials } = {}) {
  let response;
  try {
    response = await fetch(BASE_URL + path, {
      method,
      headers: { 'Content-Type': 'application/json', ...authHeader(credentials) },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch (unreachable) {
    throw new ApiError(0, 'Could not reach SkipQ. Is the backend running?');
  }

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    // The backend already phrases every refusal for the persona who caused it,
    // so the message is passed through rather than reworded here.
    throw new ApiError(response.status, payload.error || `Request failed (${response.status})`);
  }
  return payload;
}

export { BASE_URL };