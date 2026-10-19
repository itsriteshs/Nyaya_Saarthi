const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}, timeoutMs = 10000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const cancel = () => controller.abort();
  init.signal?.addEventListener("abort", cancel, { once: true });
  try {
    if (init.signal?.aborted) controller.abort();
    const response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
      signal: controller.signal,
    });
    if (!response.ok) {
      let detail = `Backend request failed (${response.status})`;
      try {
        const body: unknown = await response.json();
        if (body && typeof body === "object" && "detail" in body) {
          const value = body.detail;
          if (typeof value === "string") detail = value;
          else if (value && typeof value === "object" && "blockers" in value && Array.isArray(value.blockers)) {
            detail = value.blockers.filter((item): item is string => typeof item === "string").join("; ");
          }
        }
      } catch { /* Keep the status message. */ }
      throw new ApiError(detail, response.status);
    }
    if (response.status === 204) return undefined as T;
    try {
      const body: unknown = await response.json();
      if (body === null || typeof body !== "object" || Array.isArray(body)) {
        throw new ApiError("Backend returned an invalid response");
      }
      return body as T;
    } catch {
      throw new ApiError("Backend returned an invalid response");
    }
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error && error.name === "AbortError") throw new ApiError(init.signal?.aborted ? "Request cancelled" : "Backend request timed out");
    throw new ApiError("Could not connect to the backend");
  } finally {
    clearTimeout(timeout);
    init.signal?.removeEventListener("abort", cancel);
  }
}
