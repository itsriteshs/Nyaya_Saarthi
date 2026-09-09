import type { LanguageOption } from "@/types/nlp";

export type FactState = "provided" | "confirmed" | "inferred" | "unknown";
export type FactProvenance =
  | "USER_PROVIDED"
  | "USER_CONFIRMED"
  | "SYSTEM_INFERRED"
  | "UNKNOWN";
export type MatterStage =
  | "UNDERSTANDING"
  | "READY_FOR_REVIEW"
  | "USER_VERIFIED"
  | "GUIDANCE_GENERATED";

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
}

export interface LegalSource {
  id: string;
  title: string;
  authority: string;
  provision?: string;
  relevantPoint: string;
  sourceType: "Act" | "Rules" | "Notification" | "Guidance";
  sourceUrl?: string;
}

export interface FactLawMapping {
  id: string;
  fact: string;
  sourceId: string;
  sourceTitle: string;
  explanation: string;
}

export interface NextStep {
  id: string;
  tag: "Verify" | "Check" | "Keep" | "Respond";
  title: string;
  description: string;
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
  slot: MatterSlot;
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
  missingSlots: MatterSlot[];
  contextReadiness: {
    found: number;
    total: number;
  };
  stage: MatterStage;
  createdAt: string;
  verifiedAt?: string;
  guidance?: GuidanceResult;
  answers: Partial<Record<MatterSlot, string>>;
  currentQuestion?: ClarificationQuestion;
  messages: ConversationMessage[];
}
