const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message: string, public readonly status?: number) {
    super(message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(`${BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new ApiError(`Backend request failed (${response.status})`, response.status);
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
    if (error instanceof Error && error.name === "AbortError") throw new ApiError("Backend request timed out");
    throw new ApiError("Could not connect to the backend");
  } finally {
    clearTimeout(timeout);
  }
}
