import { apiRequest } from "./client";
import type { StoredMatter } from "./matters";

export function generateGuidance(id: string, revision: number) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/guidance`, {
    method: "POST", body: JSON.stringify({ revision }),
  }, 45000);
}

export type ModelChoice = "llama3.2-3b" | "mistral-7b" | "deterministic";
export type OutputLanguage = "english" | "hindi" | "hinglish";

export function getModels() {
  return apiRequest<{ runtime: string; models: Array<{ id: Exclude<ModelChoice, "deterministic">; displayName: string; available: boolean; status: string; default: boolean }> }>("/api/v1/models");
}

export function generateExplanation(id: string, revision: number, modelId: ModelChoice, language: OutputLanguage, regenerate = false) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/generate`, {
    method: "POST", body: JSON.stringify({ expectedRevision: revision, modelId, language, regenerate }),
  }, 330000);
}

export function completeMatter(id: string, revision: number) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/complete`, {
    method: "POST", body: JSON.stringify({ revision }),
  });
}

export function getLegalStatus() {
  return apiRequest<{ index: { indexVersion?: string; retrievalMode?: string; status?: string } }>("/api/v1/legal/status");
}
