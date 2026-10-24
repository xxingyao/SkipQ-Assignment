import { request } from './client';

export const authApi = {
  getToken: (email, password) =>
    request('/api/user/gettoken', { method: 'POST', body: { email, password } }),
};

export const dinerApi = {
  stalls: (c) => request('/api/diner/stalls', { credentials: c }),
  menu: (c, stallId) => request(`/api/diner/stalls/${stallId}/menu`, { credentials: c }),
  placeOrder: (c, stallId, lines) =>
    request('/api/diner/orders', {
      method: 'POST', credentials: c, body: { stall_id: stallId, items: lines },
    }),
  pay: (c, orderId, method) =>
    request(`/api/diner/orders/${orderId}/pay`, {
      method: 'POST', credentials: c, body: { method },
    }),
  orders: (c) => request('/api/diner/orders', { credentials: c }),
  order: (c, orderId) => request(`/api/diner/orders/${orderId}`, { credentials: c }),
  notifications: (c) => request('/api/diner/notifications', { credentials: c }),
  dismissNotifications: (c) =>
  request('/api/diner/notifications/read', { method: 'POST', credentials: c }),
};

export const vendorApi = {
  stall: (c) => request('/api/vendor/stall', { credentials: c }),
  setTrading: (c, open) =>
    request('/api/vendor/stall', {
      method: 'PATCH', credentials: c, body: { is_accepting_orders: open },
    }),
  menu: (c) => request('/api/vendor/menu', { credentials: c }),
  addItem: (c, item) =>
    request('/api/vendor/menu', { method: 'POST', credentials: c, body: item }),
  editItem: (c, itemId, changes) =>
    request(`/api/vendor/menu/${itemId}`, { method: 'PATCH', credentials: c, body: changes }),
  setAvailability: (c, itemId, available) =>
    request(`/api/vendor/menu/${itemId}/availability`, {
      method: 'PATCH', credentials: c, body: { available },
    }),
  orders: (c) => request('/api/vendor/orders', { credentials: c }),
  advance: (c, orderId, status, reason) =>
    request(`/api/vendor/orders/${orderId}/status`, {
      method: 'PATCH', credentials: c,
      body: reason ? { status, reason } : { status },
    }),
  dashboard: (c) => request('/api/vendor/dashboard', { credentials: c }),
};