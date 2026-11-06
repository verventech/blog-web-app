const BASE = "/api";
const TOKEN_KEY = "inkwell_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

function formatDetail(detail) {
  if (!detail) return null;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => `${(d.loc || []).slice(1).join(".") || "field"}: ${d.msg}`)
      .join(", ");
  }
  return JSON.stringify(detail);
}

async function request(path, { method = "GET", body, form, auth = false } = {}) {
  const headers = {};
  let payload;

  if (form) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    payload = new URLSearchParams(form).toString();
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const token = tokenStore.get();
  if (auth && token) headers.Authorization = `Bearer ${token}`;

  let res;
  try {
    res = await fetch(`${BASE}${path}`, { method, headers, body: payload });
  } catch {
    throw new ApiError("Can't reach the server. Is the backend running?", 0);
  }

  const data = await res.json().catch(() => null);
  if (!res.ok) {
    if (res.status === 401) window.dispatchEvent(new Event("inkwell:unauthorized"));
    throw new ApiError(formatDetail(data?.detail) || `Request failed (${res.status})`, res.status);
  }
  return data;
}

const userCache = new Map();

export const api = {
  login: (username, password) =>
    request("/login", { method: "POST", form: { username, password } }),
  register: (user) => request("/user", { method: "POST", body: user }),
  me: () => request("/user/me", { auth: true }),
  updateMe: (user) => request("/user/me", { method: "PUT", body: user, auth: true }),

  getUser(id) {
    if (!userCache.has(id)) {
      const p = request(`/user/${id}`).catch((e) => {
        userCache.delete(id);
        throw e;
      });
      userCache.set(id, p);
    }
    return userCache.get(id);
  },
  invalidateUser: (id) => userCache.delete(id),
  toggleFollow: (id) => request(`/user/${id}/follow`, { method: "POST", auth: true }),

  getBlogs: () => request("/blogs"),
  getBlog: (id) => request(`/blog/${id}`),
  createBlog: (blog) => request("/blog", { method: "POST", body: blog, auth: true }),
  deleteBlog: (id) => request(`/blog/${id}`, { method: "DELETE", auth: true }),
  toggleLike: (id) => request(`/blog/${id}/like`, { method: "POST", auth: true }),
  getComments: (id) => request(`/blog/${id}/comments`),
  addComment: (id, text) =>
    request(`/blog/${id}/comment`, { method: "POST", body: { text }, auth: true }),
};
