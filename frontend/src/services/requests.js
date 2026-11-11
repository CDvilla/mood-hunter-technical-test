import { getToken } from "./auth.js";
import { apiFetch } from "./api.js";

function authenticatedFetch(path, options = {}) {
  const token = getToken();

  if (!token) {
    throw new Error("Tu sesión no está activa. Inicia sesión nuevamente.");
  }

  return apiFetch(path, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });
}

export function getRequests({
  filters = {},
  page = 1,
  pageSize = 10,
  signal,
} = {}) {
  const params = new URLSearchParams({ page, page_size: pageSize });

  for (const [key, value] of Object.entries(filters)) {
    if (value) {
      params.set(key, value);
    }
  }

  return authenticatedFetch(`/requests/?${params}`, { signal });
}

export function getStatuses({ signal } = {}) {
  return authenticatedFetch("/statuses/", { signal });
}

export async function getRequestSummary({ startDate, endDate, signal }) {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 20_000);
  const abortFromCaller = () => controller.abort();

  signal?.addEventListener("abort", abortFromCaller, { once: true });

  try {
    return await authenticatedFetch(`/requests/summary/?${params}`, {
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeoutId);
    signal?.removeEventListener("abort", abortFromCaller);
  }
}

export function updateRequestStatus(id, nextStatus, { signal } = {}) {
  return authenticatedFetch(`/requests/${id}/`, {
    method: "PATCH",
    body: JSON.stringify({ status: nextStatus }),
    signal,
  });
}
