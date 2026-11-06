const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function endpoint(path) {
  return `${API_BASE}${path}`;
}

async function errorMessage(response) {
  try {
    const payload = await response.json();
    const detail = payload?.detail;
    if (typeof detail === "string") return detail;
    if (detail?.message) return detail.message;
    if (Array.isArray(detail)) {
      return detail
        .map((item) => item?.msg ?? JSON.stringify(item))
        .join("; ");
    }
    return JSON.stringify(payload);
  } catch {
    return `Request failed with HTTP ${response.status}`;
  }
}

async function request(path, options = {}) {
  const response = await fetch(endpoint(path), {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });

  if (!response.ok) {
    throw new Error(await errorMessage(response));
  }
  return response.json();
}

export function getCatalog() {
  return request("/api/catalog");
}

export function getHealth() {
  return request("/api/health");
}

export function getSamples() {
  return request("/api/samples");
}

export function generateNotebook(payload) {
  return request("/api/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function validateSnippet(code, section = "manual") {
  return request("/api/validate", {
    method: "POST",
    body: JSON.stringify({ code, section }),
  });
}

export function apiBase() {
  return API_BASE;
}

export function sampleUrl(path) {
  return endpoint(path);
}

export function notebookBlob(notebook) {
  return new Blob([JSON.stringify(notebook, null, 2)], {
    type: "application/x-ipynb+json",
  });
}

export function downloadNotebook(notebook, filename) {
  const url = URL.createObjectURL(notebookBlob(notebook));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "generated_notebook.ipynb";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
}
