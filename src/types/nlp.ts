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
