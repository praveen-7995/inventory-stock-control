const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, isForm = false, token, raw = false } = {}) {
  const headers = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body && !isForm) headers["Content-Type"] = "application/json";

  const res = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: isForm ? body : body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const data = await res.json();
      message = data.detail || message;
    } catch {
      // ignore parse errors, keep default message
    }
    throw new ApiError(message, res.status);
  }

  if (raw) return res;
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  login: (email, password) => request("/auth/login", { method: "POST", body: { email, password } }),
  me: (token) => request("/auth/me", { token }),

  listItems: (token, params) => {
    const qs = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== "" && v !== null))
    ).toString();
    return request(`/items?${qs}`, { token });
  },
  getItem: (token, id) => request(`/items/${id}`, { token }),
  createItem: (token, payload) => request("/items", { method: "POST", body: payload, token }),
  updateItem: (token, id, payload) => request(`/items/${id}`, { method: "PATCH", body: payload, token }),
  archiveItem: (token, id) => request(`/items/${id}/archive`, { method: "POST", token }),
  restoreItem: (token, id) => request(`/items/${id}/restore`, { method: "POST", token }),
  addNote: (token, id, note) => request(`/items/${id}/notes`, { method: "POST", body: { note }, token }),
  getHistory: (token, id) => request(`/items/${id}/history`, { token }),

  listCategories: (token) => request("/categories", { token }),
  createCategory: (token, name) => request("/categories", { method: "POST", body: { name }, token }),

  listLocations: (token) => request("/locations", { token }),
  listMyLocations: (token) => request("/locations/mine", { token }),
  createLocation: (token, name) => request("/locations", { method: "POST", body: { name }, token }),
  listAssignments: (token) => request("/assignments", { token }),
  createAssignment: (token, user_id, location_id) =>
    request("/assignments", { method: "POST", body: { user_id, location_id }, token }),
  deleteAssignment: (token, id) => request(`/assignments/${id}`, { method: "DELETE", token }),
  listStaff: (token) => request("/staff", { token }),

  listUsers: (token) => request("/users", { token }),
  createUser: (token, payload) => request("/users", { method: "POST", body: payload, token }),

  createMovement: (token, payload) => request("/movements", { method: "POST", body: payload, token }),
  listMovementsForItem: (token, itemId) => request(`/movements/item/${itemId}`, { token }),

  getDashboard: (token) => request("/dashboard", { token }),

  listAlerts: (token) => request("/alerts", { token }),
  dismissAlert: (token, itemId) => request(`/alerts/${itemId}/dismiss`, { method: "POST", token }),

  importItems: (token, file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/import/items", { method: "POST", body: form, isForm: true, token });
  },
  importReceipts: (token, file) => {
    const form = new FormData();
    form.append("file", file);
    return request("/import/receipts", { method: "POST", body: form, isForm: true, token });
  },
  exportStockUrl: () => `${API_URL}/export/stock`,
  exportStock: async (token) => {
    const res = await request("/export/stock", { token, raw: true });
    return res.blob();
  },
};

export { ApiError };
