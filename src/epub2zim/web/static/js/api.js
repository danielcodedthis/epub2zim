// api.js: tiny wrapper around fetch() for the REST API (see docs/api.md).
// Every function returns the parsed JSON, or throws an Error with a friendly message.

async function request(method, url, body) {
  const options = { method, headers: {} };
  if (body instanceof FormData) {
    options.body = body;                        // file upload: browser sets the headers
  } else if (body !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }
  const res = await fetch(url, options);
  let data = null;
  try { data = await res.json(); } catch (e) { /* empty or non-JSON answer */ }
  if (!res.ok) {
    let msg = data && data.detail ? data.detail : `Request failed (${res.status})`;
    if (Array.isArray(msg)) msg = msg.map((d) => d.msg).join("; ");   // FastAPI validation errors
    throw new Error(msg);
  }
  return data;
}

export const api = {
  config: () => request("GET", "/api/config"),
  mcpKey: () => request("GET", "/api/config/mcp-key"),

  projects: () => request("GET", "/api/projects"),
  upload: (file) => { const f = new FormData(); f.append("file", file); return request("POST", "/api/projects", f); },
  project: (id) => request("GET", `/api/projects/${id}`),
  remove: (id) => request("DELETE", `/api/projects/${id}`),

  saveSettings: (id, settings) => request("PUT", `/api/projects/${id}/settings`, settings),
  saveTitles: (id, text) => request("PUT", `/api/projects/${id}/titles`, { text }),
  saveAliases: (id, text) => request("PUT", `/api/projects/${id}/aliases`, { text }),

  pages: (id, start, count = 3) => request("GET", `/api/projects/${id}/pages?start=${start}&count=${count}&chars=700`),
  find: (id, q, regex = false) => request("GET", `/api/projects/${id}/find?q=${encodeURIComponent(q)}&regex=${regex}`),
  suggest: (id, method, level = 2, pattern = "") => request("POST", `/api/projects/${id}/suggest`, { method, level, pattern }),

  coverUrl: (id) => `/api/projects/${id}/cover?t=${Date.now()}`,
  uploadCover: (id, file) => { const f = new FormData(); f.append("file", file); return request("POST", `/api/projects/${id}/cover`, f); },
  removeCover: (id) => request("DELETE", `/api/projects/${id}/cover`),

  preview: (id) => request("POST", `/api/projects/${id}/preview`),
  build: (id) => request("POST", `/api/projects/${id}/build`),
  downloadUrl: (id, file) => `/api/projects/${id}/download/${encodeURIComponent(file)}`,
};
