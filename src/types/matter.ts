import type { LanguageOption } from "@/types/nlp";

export type FactState = "provided" | "confirmed" | "inferred" | "unknown";
export type FactProvenance =
  | "USER_PROVIDED"
  | "USER_CONFIRMED"
  | "SYSTEM_INFERRED"
  | "UNKNOWN";
export type MatterStage =
  | "DRAFT"
  | "UNDERSTANDING"
  | "NEEDS_CLARIFICATION"
  | "READY_FOR_REVIEW"
  | "USER_VERIFIED"
  | "GUIDANCE_GENERATED"
  | "COMPLETED";

export type MatterSlot =
  | "vehicle_type"
  | "location"
  | "enforcement_status"
  | "licence_action";

export interface MatterFact {
  id: string;
  key: string;
  label: string;
  value: string;
  state: FactState;
  provenance: FactProvenance;
  confirmed: boolean;
  requiresConfirmation?: boolean;
  normalizedValue?: string;
  normalizedId?: string;
  sourceMessageId?: string;
  extractionMethod?: string;
  resolutionStatus?: "resolved" | "ambiguous" | "unresolved";
  updatedAt?: string;
}

export interface LegalSource {
  id: string;
  title: string;
  authority: string;
  provision?: string;
  relevantPoint: string;
  sourceType: "Act" | "Rules" | "Notification" | "Guidance";
  sourceUrl?: string;
  evidenceId?: string;
  reviewStatus?: string;
  admissibility?: string;
}

export interface FactLawMapping {
  id: string;
  fact: string;
  sourceId: string;
  sourceTitle: string;
  explanation: string;
  evidenceId?: string;
}

export interface NextStep {
  id: string;
  tag: "Verify" | "Check" | "Keep" | "Respond";
  title: string;
  description: string;
  evidenceId?: string;
}

export interface GuidanceResult {
  generatedAt: string;
  directAnswer: string;
  qualification: string;
  sources: LegalSource[];
  mappings: FactLawMapping[];
  uncertainties: string[];
  nextSteps: NextStep[];
  suggestedQuestions: string[];
  metadata?: {
    indexVersion?: string;
    retrievalMode?: string;
    jurisdictionId?: string | null;
    eventDate?: string | null;
    ruleEvaluations?: Array<{ ruleId: string; status: string; reasons: string[] }>;
    generationMethod?: string;
    requestedModel?: string;
    requestedLanguage?: string;
    fallbackUsed?: boolean;
    failureReason?: string;
    evidencePackageId?: string;
  };
}

export interface ConversationMessage {
  id: string;
  speaker: "user" | "assistant";
  text: string;
}

export interface ClarificationOption {
  label: string;
  value: string;
}

export interface ClarificationQuestion {
  id?: string;
  slot: string;
  question: string;
  type: "options" | "text";
  options?: ClarificationOption[];
  why: string;
}

export interface MatterContext {
  id: string;
  originalText: string;
  language: LanguageOption;
  intent: {
    label: string;
    descriptor: string;
  };
  facts: MatterFact[];
  missingSlots: string[];
  contextReadiness: {
    found: number;
    total: number;
  };
  stage: MatterStage;
  createdAt: string;
  verifiedAt?: string;
  guidance?: GuidanceResult;
  answers: Record<string, string>;
  currentQuestion?: ClarificationQuestion;
  messages: ConversationMessage[];
  nlpAnalysis?: import("@/types/nlp").NlpAnalysis;
  conversation?: {
    askedSlots: string[];
    unknownSlots: string[];
    contradictions: Array<{ id: string; slot: string; previous: MatterFact; candidate: MatterFact; kind?: string; resolved: boolean }>;
    factHistory: Array<Record<string, unknown>>;
    displayLanguage: string;
    reviewEligible: boolean;
    verificationEligible?: boolean;
    confirmationPending?: string[];
    unresolvedRequirements: Array<{ slot: string; condition: string; reason: string }>;
    ambiguousSlots?: string[];
    urgentAssistance: boolean;
    unknownsAcknowledged?: boolean;
  };
  revision?: number;
}
