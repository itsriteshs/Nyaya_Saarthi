import type { MatterContext } from "@/types/matter";
import type { LanguageOption } from "@/types/nlp";
import { apiRequest } from "./client";

export interface StoredMatter extends MatterContext {
  updatedAt: string;
  schemaVersion: number;
  revision: number;
}

export type MatterUpdate = Partial<Pick<StoredMatter,
  "intent" | "facts" | "missingSlots" | "contextReadiness" | "stage" | "verifiedAt" |
  "guidance" | "answers" | "currentQuestion" | "messages">> & { revision: number };

export function createMatter(originalText: string, language: LanguageOption) {
  return apiRequest<StoredMatter>("/api/v1/matters", { method: "POST", body: JSON.stringify({ originalText, language }) });
}
export function getMatter(id: string) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}`);
}
export function updateMatter(id: string, update: MatterUpdate) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}`, { method: "PATCH", body: JSON.stringify(update) });
}
export function deleteMatter(id: string) {
  return apiRequest<void>(`/api/v1/matters/${encodeURIComponent(id)}`, { method: "DELETE" });
}
