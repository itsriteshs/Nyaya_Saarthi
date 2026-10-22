import { apiRequest } from "./client";
import type { StoredMatter } from "./matters";
import { localReferenceDatetime } from "./nlp";

export function submitAnswer(id: string, revision: number, questionId: string, answer: string, messageId: string) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/answers`, {
    method: "POST", body: JSON.stringify({ revision, questionId, answer, messageId, referenceDatetime: localReferenceDatetime() }),
  }, 100000);
}
export function editMatterFact(id: string, factId: string, revision: number, value: string) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/facts/${encodeURIComponent(factId)}`, {
    method: "PATCH", body: JSON.stringify({ revision, value }),
  });
}
export function confirmMatterFact(id: string, factId: string, revision: number) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/facts/${encodeURIComponent(factId)}/confirm`, {
    method: "POST", body: JSON.stringify({ revision }),
  });
}
export function verifyStructuredMatter(id: string, revision: number, acknowledgeUnknowns: boolean) {
  return apiRequest<StoredMatter>(`/api/v1/matters/${encodeURIComponent(id)}/verify`, {
    method: "POST", body: JSON.stringify({ revision, acknowledgeUnknowns }),
  });
}
