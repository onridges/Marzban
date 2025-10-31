import { FetchOptions, $fetch as ohMyFetch } from "ofetch";
import { getAuthToken, setAuthToken, removeAuthToken } from "utils/authStorage";

// Robust base URL: fallback for dev when VITE_BASE_API is unset
const fallbackBase = import.meta.env.DEV ? "http://127.0.0.1:8000/api/" : "/api/";
const baseURL = (import.meta as any).env?.VITE_BASE_API || fallbackBase;

export const $fetch = ohMyFetch.create({
  baseURL,
});

// Simple in-flight refresh coordination to avoid parallel refresh storms
let refreshingPromise: Promise<string | null> | null = null;

const refreshAccessToken = async (): Promise<string | null> => {
  if (refreshingPromise) return refreshingPromise;
  const rt = localStorage.getItem('refresh_token');
  if (!rt) return null;
  refreshingPromise = (async () => {
    try {
      const resp = await $fetch<{ access_token?: string }>("/token/refresh", {
        method: "POST",
        body: { refresh_token: rt },
        headers: { "Content-Type": "application/json" },
        // never attach Authorization for refresh
      });
      const newToken = resp?.access_token || null;
      if (newToken) setAuthToken(newToken);
      return newToken;
    } catch (e) {
      // refresh failed; clear auth and surface original 401
      removeAuthToken();
      return null;
    } finally {
      refreshingPromise = null;
    }
  })();
  return refreshingPromise;
};

export const fetcher = async <T = any>(
  url: string,
  ops: FetchOptions<"json"> = {}
): Promise<T> => {
  // Avoid attaching Authorization for public auth endpoints
  const isPublicAuth = url.endsWith('/token') || url.endsWith('/admin/token') || url.endsWith('/register') || url.endsWith('/token/refresh');
  const token = getAuthToken();
  const initialHeaders = {
    ...(ops?.headers || {}),
    ...(token && !isPublicAuth ? { Authorization: `Bearer ${token}` } : {}),
  } as Record<string, any>;

  const attempt = async (headers: Record<string, any>) => {
    return $fetch<T>(url, { ...ops, headers });
  };

  try {
    return await attempt(initialHeaders);
  } catch (err: any) {
    // Ignore aborts entirely; caller hooks already handle them
    const aborted = err?.name === 'AbortError' || err?.code === 20 || err?.message?.includes('aborted');
    if (aborted) throw err;

    const status = err?.response?.status;
    // On 401, try refresh once then retry original request
    if (status === 401 && !isPublicAuth) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        const retryHeaders = {
          ...(ops?.headers || {}),
          Authorization: `Bearer ${newToken}`,
        } as Record<string, any>;
        return attempt(retryHeaders);
      }
    }
    throw err;
  }
};

export const fetch = fetcher;
