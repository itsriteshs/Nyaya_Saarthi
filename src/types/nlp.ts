export type LanguageOption = "auto" | "english" | "hindi" | "hinglish";

export type TopicId =
  | "traffic"
  | "challan"
  | "licence"
  | "registration"
  | "insurance"
  | "accident";

export interface MotorLawTopic {
  id: TopicId;
  label: string;
  placeholder: string;
  example: string;
}

export interface ExamplePrompt {
  id: string;
  text: string;
}

export interface NlpFact {
  label: string;
  value: string;
  source: "user" | "inferred";
}

export interface MockNlpResult {
  inputText: string;
  detectedIssue: {
    label: string;
    description: string;
  };
  extractedFacts: NlpFact[];
  missingInformation: string[];
  readiness: {
    found: number;
    total: number;
  };
  nextQuestion: string;
  visibleSignals: string[];
}

export interface NlpAnalysis {
  extractionMetadata?: {
    method?: string;
    fallbackUsed?: boolean;
    modelCalled?: boolean;
    requestedModel?: string;
    failureReason?: string;
    rejectedMentions?: Array<{ slot: string; reason: string }>;
  };
  inputText: string;
  normalizedText: string;
  language: {
    requestedLanguage: LanguageOption;
    detectedLanguage: "english" | "hindi" | "hinglish" | "mixed" | "uncertain";
    confidenceCategory: "high" | "medium" | "low";
    evidence: string;
    candidateLanguage?: string;
  };
  intent: {
    id: string;
    name: string;
    domain: string;
    score: number;
    scoreType: string;
    marginGap: number;
    alternatives: Array<{ id: string; name: string; score: number }>;
    needsClarification: boolean;
    modelVersion: string;
  };
  entities: Array<{
    type: string;
    text: string;
    value: string;
    normalizedValue?: string;
    normalizedId?: string;
    status: "resolved" | "ambiguous" | "unresolved";
    vocabularySource?: string;
    alternatives: string[];
    unit?: string;
    approximate?: boolean;
    start: number;
    end: number;
    method: string;
    confidence?: number;
  }>;
  missingSlots: Array<{ slot: string; label: string; priority: number; question: string; reason: string }>;
  unresolvedSlots: Array<{ slot: string; reason: string; condition: string; present?: boolean }>;
  readiness: { found: number; total: number; percentage: number; status: string };
  warnings: string[];
  modelVersion: string;
}
