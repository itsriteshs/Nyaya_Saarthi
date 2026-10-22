import { apiRequest } from "./client";
import type { LanguageOption, MockNlpResult, NlpAnalysis } from "@/types/nlp";

export function localReferenceDatetime(): string {
  const now = new Date();
  const offset = -now.getTimezoneOffset();
  const sign = offset >= 0 ? "+" : "-";
  const hours = String(Math.floor(Math.abs(offset) / 60)).padStart(2, "0");
  const minutes = String(Math.abs(offset) % 60).padStart(2, "0");
  const local = new Date(now.getTime() + offset * 60_000).toISOString().slice(0, 19);
  return `${local}${sign}${hours}:${minutes}`;
}

export function analyzeText(text: string, language: LanguageOption, signal?: AbortSignal) {
  return apiRequest<NlpAnalysis>("/api/v1/nlp/analyze", {
    method: "POST",
    body: JSON.stringify({ text, language, referenceDatetime: localReferenceDatetime() }),
    signal,
  }, 40000);
}

export function toPreview(result: NlpAnalysis): MockNlpResult {
  return {
    inputText: result.inputText,
    detectedIssue: {
      label: result.intent.needsClarification ? "Issue needs confirmation" : result.intent.name.replaceAll("_", " "),
      description: `${result.intent.needsClarification ? "Possible topic: " + result.intent.name.replaceAll("_", " ") + " · " : ""}${result.intent.domain} · ${result.intent.id}${result.intent.needsClarification ? " · Needs confirmation" : ""}`,
    },
    extractedFacts: result.entities.map((entity) => ({
      label: entity.type.replaceAll("_", " "),
      value: entity.normalizedValue && entity.normalizedValue !== entity.text
        ? `${entity.text} → ${entity.normalizedValue}` : entity.text,
      source: "user",
    })),
    missingInformation: result.intent.needsClarification ? ["Confirm the issue first"] : result.missingSlots.map((slot) => slot.label),
    readiness: result.intent.needsClarification ? { found: 0, total: 1 } : result.readiness,
    nextQuestion: result.intent.needsClarification ? "Confirm the issue before issue-specific questions." : result.missingSlots[0]?.question ??
      (result.unresolvedSlots.length ? "Some requirements need clarification." : "Review the extracted facts."),
    visibleSignals: [
      `Detected: ${result.language.detectedLanguage}`,
      `Intent: ${result.intent.id}`,
      ...result.warnings.slice(0, 1),
    ],
  };
}
