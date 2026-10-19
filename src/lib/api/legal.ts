import { apiRequest } from "./client";
import type { StoredMatter } from "./matters";

export function generateGuidance(id: string, revision: number) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/guidance`, {
    method: "POST", body: JSON.stringify({ revision }),
  }, 45000);
}

export function completeMatter(id: string, revision: number) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/complete`, {
    method: "POST", body: JSON.stringify({ revision }),
  });
}

export function getLegalStatus() {
  return apiRequest<{ index: { indexVersion?: string; retrievalMode?: string; status?: string } }>("/api/v1/legal/status");
}
