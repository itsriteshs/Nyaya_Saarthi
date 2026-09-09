import { clarificationQuestions } from "@/data/clarification-questions";
import { defaultMatter } from "@/data/mock-matters";
import { analyzeSituation } from "@/lib/mock-nlp";
import type {
  ClarificationQuestion,
  ConversationMessage,
  MatterContext,
  MatterFact,
  MatterSlot,
} from "@/types/matter";
import type { LanguageOption } from "@/types/nlp";

// Frontend interaction prototype.
// The real intent, entity extraction, missing-slot detection
// and adaptive-question selection will come from FastAPI/NLP services.

const requiredSpeedingSlots: MatterSlot[] = ["vehicle_type", "location", "enforcement_status"];

export function createMatterContext(
  originalText = defaultMatter.originalText,
  language: LanguageOption = defaultMatter.language,
): MatterContext {
  const analysis = analyzeSituation(originalText);
  const lower = originalText.toLowerCase();
  const missingSlots = getInitialMissingSlots(lower, analysis.extractedFacts);
  const currentQuestion = getNextQuestion(missingSlots);

  const facts = buildInitialFacts(analysis.extractedFacts, missingSlots);
  const readiness = calculateReadiness(facts);

  return {
    id: createMatterId(),
    originalText,
    language,
    intent: {
      label: analysis.detectedIssue.label.replace("Speed or traffic enforcement", "Possible speeding / traffic violation"),
      descriptor: getDescriptor(analysis.detectedIssue.label),
    },
    facts,
    missingSlots,
    contextReadiness: {
      found: readiness.found,
      total: readiness.total,
    },
    stage: missingSlots.length > 0 ? "UNDERSTANDING" : "READY_FOR_REVIEW",
    createdAt: new Date().toISOString(),
    answers: {},
    currentQuestion,
    messages: [
      {
        id: "user-initial",
        speaker: "user",
        text: originalText,
      },
      {
        id: "assistant-intro",
        speaker: "assistant",
        text: "I can help work out what may apply. I need a couple of details first.",
      },
    ],
  };
}

export function answerCurrentQuestion(context: MatterContext, answer: string): MatterContext {
  if (!context.currentQuestion || !answer.trim()) {
    return context;
  }

  const slot = context.currentQuestion.slot;
  const cleanAnswer = answer.trim();
  const nextAnswers = {
    ...context.answers,
    [slot]: cleanAnswer,
  };
  const nextMissingSlots = context.missingSlots.filter((missingSlot) => missingSlot !== slot);
  const answeredFacts = factsFromAnswer(slot, cleanAnswer);
  const nextFacts = addInferences(
    answeredFacts.reduce((facts, fact) => upsertFact(facts, fact), context.facts),
    slot,
    cleanAnswer,
  );
  const nextQuestion = getNextQuestion(nextMissingSlots);
  const messages = appendAnswerMessages(context.messages, cleanAnswer, nextQuestion);
  const readiness = calculateReadiness(nextFacts);

  return {
    ...context,
    answers: nextAnswers,
    missingSlots: nextMissingSlots,
    facts: nextFacts,
    contextReadiness: {
      found: readiness.found,
      total: readiness.total,
    },
    stage: nextMissingSlots.length > 0 ? "UNDERSTANDING" : "READY_FOR_REVIEW",
    currentQuestion: nextQuestion,
    messages,
  };
}

export function getReadiness(context: MatterContext) {
  const { found, total } = calculateReadiness(context.facts);

  return {
    found,
    total,
    percent: Math.round((found / total) * 100),
    complete: found === total,
  };
}

export function confirmFact(context: MatterContext, factId: string): MatterContext {
  const facts = context.facts.map((fact) =>
    fact.id === factId
      ? {
          ...fact,
          state: "confirmed" as const,
          provenance: "USER_CONFIRMED" as const,
          confirmed: true,
          requiresConfirmation: false,
        }
      : fact,
  );
  const readiness = calculateReadiness(facts);

  return {
    ...context,
    facts,
    contextReadiness: {
      found: readiness.found,
      total: readiness.total,
    },
  };
}

export function updateFactValue(context: MatterContext, factId: string, value: string): MatterContext {
  const facts = context.facts.map((fact) =>
    fact.id === factId
      ? {
          ...fact,
          value: value.trim() || fact.value,
          state: "confirmed" as const,
          provenance: "USER_CONFIRMED" as const,
          confirmed: true,
          requiresConfirmation: false,
        }
      : fact,
  );
  const readiness = calculateReadiness(facts);

  return {
    ...context,
    facts,
    guidance: undefined,
    verifiedAt: undefined,
    stage: "READY_FOR_REVIEW",
    contextReadiness: {
      found: readiness.found,
      total: readiness.total,
    },
  };
}

export function verifyMatter(context: MatterContext): MatterContext {
  return {
    ...context,
    stage: "USER_VERIFIED",
    verifiedAt: new Date().toISOString(),
    facts: context.facts.map((fact) =>
      fact.provenance === "USER_PROVIDED"
        ? {
            ...fact,
            state: "confirmed",
            provenance: "USER_CONFIRMED",
            confirmed: true,
          }
        : fact,
    ),
  };
}

function getInitialMissingSlots(originalText: string, facts: Array<{ label: string }>) {
  if (/(licence|license).{0,30}(took|kept|seized|impound)/.test(originalText)) {
    return ["licence_action", "location", "enforcement_status"] as MatterSlot[];
  }

  const labels = facts.map((fact) => fact.label.toLowerCase());
  return requiredSpeedingSlots.filter((slot) => {
    if (slot === "vehicle_type") {
      return !labels.includes("vehicle type");
    }

    if (slot === "location") {
      return !labels.includes("location") && !labels.includes("road context");
    }

    if (slot === "enforcement_status") {
      return !labels.includes("challan status") && !labels.includes("authority");
    }

    return true;
  });
}

function buildInitialFacts(extracted: Array<{ label: string; value: string }>, missingSlots: MatterSlot[]) {
  const facts: MatterFact[] = extracted
    .filter((fact) => fact.label !== "User description")
    .map((fact) => ({
      id: normalizeFactId(fact.label),
      key: normalizeFactId(fact.label),
      label: normalizeFactLabel(fact.label),
      value: fact.value,
      state: "provided",
      provenance: "USER_PROVIDED",
      confirmed: false,
    }));

  const unknownFacts: MatterFact[] = [
    missingSlots.includes("vehicle_type") && {
      id: "vehicle_type",
      key: "vehicle_type",
      label: "Vehicle",
      value: "Not answered yet",
      state: "unknown",
      provenance: "UNKNOWN",
      confirmed: false,
    },
    missingSlots.includes("location") && {
      id: "location",
      key: "location",
      label: "Location",
      value: "Not answered yet",
      state: "unknown",
      provenance: "UNKNOWN",
      confirmed: false,
    },
    missingSlots.includes("enforcement_status") && unknownFact("police_stop", "Police interaction"),
    missingSlots.includes("enforcement_status") && unknownFact("challan_status", "Challan"),
    missingSlots.includes("licence_action") && {
      id: "licence_action",
      key: "licence_action",
      label: "Licence action",
      value: "Not answered yet",
      state: "unknown",
      provenance: "UNKNOWN",
      confirmed: false,
    },
  ].filter(Boolean) as MatterFact[];

  return mergeFacts([...facts, ...unknownFacts]);
}

function factsFromAnswer(slot: MatterSlot, answer: string): MatterFact[] {
  if (slot === "enforcement_status") {
    const lower = answer.toLowerCase();
    const stopped = lower.includes("stopped") || lower.includes("police") || lower.includes("both");
    const noChallan = lower.includes("no challan") || lower.includes("neither");
    const received = lower.includes("received challan") || lower.includes("both");

    return [
      {
        id: "police_stop",
        key: "police_stop",
        label: "Police interaction",
        value: stopped ? "Stopped by police" : "Not reported",
        state: "provided",
        provenance: "USER_PROVIDED",
        confirmed: false,
      },
      {
        id: "challan_status",
        key: "challan_status",
        label: "Challan",
        value: noChallan ? "None reported" : received ? "Challan reported" : answer,
        state: "provided",
        provenance: "USER_PROVIDED",
        confirmed: false,
      },
    ];
  }

  return [factFromAnswer(slot, answer)];
}

function factFromAnswer(slot: MatterSlot, answer: string): MatterFact {
  const labels: Record<MatterSlot, string> = {
    vehicle_type: "Vehicle",
    location: "Location",
    enforcement_status: "Police interaction",
    licence_action: "Licence action",
  };

  return {
    id: slot,
    key: slot,
    label: labels[slot],
    value: normalizeAnswer(slot, answer),
    state: "provided",
    provenance: "USER_PROVIDED",
    confirmed: false,
  };
}

function upsertFact(facts: MatterFact[], nextFact: MatterFact) {
  const exists = facts.some((fact) => fact.id === nextFact.id);

  if (!exists) {
    return mergeFacts([...facts, nextFact]);
  }

  return mergeFacts(facts.map((fact) => (fact.id === nextFact.id ? nextFact : fact)));
}

function mergeFacts(facts: MatterFact[]) {
  const order = [
    "speed",
    "vehicle_type",
    "location",
    "road_type",
    "authority",
    "police_stop",
    "challan_status",
    "enforcement_status",
    "licence_action",
    "document",
  ];
  return [...facts].sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
}

function unknownFact(id: string, label: string): MatterFact {
  return {
    id,
    key: id,
    label,
    value: "Not answered yet",
    state: "unknown",
    provenance: "UNKNOWN",
    confirmed: false,
  };
}

function addInferences(facts: MatterFact[], slot: MatterSlot, answer: string) {
  if (slot !== "location" || !/expressway/i.test(answer)) {
    return facts;
  }

  return upsertFact(facts, {
    id: "road_type",
    key: "road_type",
    label: "Road type",
    value: "Expressway",
    state: "inferred",
    provenance: "SYSTEM_INFERRED",
    confirmed: false,
    requiresConfirmation: true,
  });
}

function normalizeAnswer(slot: MatterSlot, answer: string) {
  if (slot === "enforcement_status" && /stopped/i.test(answer) && /no challan|none|neither/i.test(answer)) {
    return "Stopped by police; no challan reported";
  }

  return answer;
}

function calculateReadiness(facts: MatterFact[]) {
  const relevantFacts = facts.filter((fact) => fact.id !== "authority" && fact.id !== "document");
  const total = relevantFacts.length;
  const found = relevantFacts.filter(
    (fact) => fact.state !== "unknown" && !fact.requiresConfirmation,
  ).length;

  return {
    found,
    total,
  };
}

function createMatterId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }

  return `matter-${Date.now()}`;
}

function normalizeFactId(label: string) {
  if (label === "Speed") {
    return "speed";
  }

  if (label === "Vehicle type") {
    return "vehicle_type";
  }

  if (label === "Challan status") {
    return "enforcement_status";
  }

  if (label === "Document mentioned") {
    return "document";
  }

  return label.toLowerCase().replaceAll(" ", "_");
}

function normalizeFactLabel(label: string) {
  if (label === "Vehicle type") {
    return "Vehicle";
  }

  if (label === "Challan status") {
    return "Police interaction";
  }

  if (label === "Document mentioned") {
    return "Document";
  }

  return label;
}

function getNextQuestion(missingSlots: MatterSlot[]): ClarificationQuestion | undefined {
  const nextSlot = missingSlots[0];
  return nextSlot ? clarificationQuestions[nextSlot] : undefined;
}

function appendAnswerMessages(
  messages: ConversationMessage[],
  answer: string,
  nextQuestion?: ClarificationQuestion,
) {
  const nextMessages: ConversationMessage[] = [
    ...messages,
    {
      id: `user-${messages.length + 1}`,
      speaker: "user",
      text: answer,
    },
  ];

  if (nextQuestion) {
    nextMessages.push({
      id: `assistant-${messages.length + 2}`,
      speaker: "assistant",
      text: nextQuestion.question,
    });
  } else {
    nextMessages.push({
      id: `assistant-${messages.length + 2}`,
      speaker: "assistant",
      text: "Your situation is ready to review. Legal applicability will be checked after you verify the situation.",
    });
  }

  return nextMessages;
}

function getDescriptor(issue: string) {
  if (issue.includes("Licence")) {
    return "Licence / document handling";
  }

  if (issue.includes("Accident")) {
    return "Accident context";
  }

  if (issue.includes("Challan")) {
    return "Traffic enforcement";
  }

  return "Traffic Enforcement";
}
