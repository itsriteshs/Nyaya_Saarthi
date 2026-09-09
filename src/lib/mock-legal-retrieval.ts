import type { GuidanceResult, MatterContext, MatterFact } from "@/types/matter";

// Frontend prototype only.
// Production legal retrieval will be performed by the FastAPI
// hybrid retrieval/RAG pipeline over verified official sources.
export function mockLegalRetrieval(matter: MatterContext): GuidanceResult {
  const vehicle = getFact(matter.facts, "vehicle_type") ?? "the vehicle";
  const speed = getFact(matter.facts, "speed") ?? "the reported speed";
  const location = getFact(matter.facts, "location") ?? "the stated location";
  const roadType = getFact(matter.facts, "road_type");
  const challan = getFact(matter.facts, "challan_status");

  const sources = [
    {
      id: "mva-1988",
      title: "Motor Vehicles Act, 1988",
      authority: "Government of India",
      provision: "Section / provision placeholder",
      relevantPoint:
        "Provides the statutory framework for motor vehicle regulation and enforcement.",
      sourceType: "Act" as const,
    },
    {
      id: "cmvr",
      title: "Central Motor Vehicles Rules",
      authority: "Government of India",
      provision: "Rule placeholder",
      relevantPoint:
        "Supports vehicle classification, compliance requirements and related procedures.",
      sourceType: "Rules" as const,
    },
    {
      id: "speed-notification",
      title: "Applicable road or transport authority notification",
      authority: "Relevant transport or road authority",
      provision: "Notification placeholder",
      relevantPoint:
        "Speed restrictions may be notified for vehicle classes and road contexts.",
      sourceType: "Notification" as const,
    },
  ];

  return {
    generatedAt: new Date().toISOString(),
    directAnswer: `Based on the situation you confirmed, travelling at approximately ${speed} may fall within speeding provisions if that speed exceeded the notified limit applicable to ${vehicle.toLowerCase()} and the relevant road segment.`,
    qualification:
      "The exact applicability depends on the speed restriction officially notified for that road segment and vehicle category.",
    sources,
    mappings: [
      {
        id: "speed-context",
        fact: `You reported ${speed} in ${vehicle.toLowerCase()}${location ? ` at ${location}` : ""}.`,
        sourceId: "speed-notification",
        sourceTitle: "Applicable road or transport authority notification",
        explanation:
          "If the applicable notified limit is below the reported speed, the situation may constitute overspeeding.",
      },
      {
        id: "vehicle-context",
        fact: `Vehicle category: ${vehicle}.`,
        sourceId: "cmvr",
        sourceTitle: "Central Motor Vehicles Rules",
        explanation:
          "Vehicle category can affect which restrictions and procedures are relevant.",
      },
    ],
    uncertainties: [
      "The exact notified speed limit for the specific road segment has not yet been conclusively established.",
      challan === "None reported"
        ? "No written challan has been reported by the user."
        : "The final challan or notice details may still need official verification.",
      roadType
        ? `Road type used for context: ${roadType}.`
        : "Road type was not separately established.",
    ],
    nextSteps: [
      {
        id: "verify-speed-limit",
        tag: "Verify",
        title: "Verify the applicable speed restriction",
        description:
          "Check the official speed restriction for the relevant road segment and your vehicle category.",
      },
      {
        id: "check-challan",
        tag: "Check",
        title: "Check whether an eChallan was generated",
        description: "Use the appropriate official eChallan service if applicable.",
      },
      {
        id: "preserve-documents",
        tag: "Keep",
        title: "Keep documents from the police interaction",
        description: "Preserve any receipt, notice or acknowledgement that was provided.",
      },
      {
        id: "contest-procedure",
        tag: "Respond",
        title: "Review contest procedures if needed",
        description:
          "If you later receive a challan you disagree with, review the official contest or grievance procedure for that notice.",
      },
    ],
    suggestedQuestions: [
      "Why does vehicle type matter?",
      "Which rule is relevant?",
      "What if I receive a challan later?",
      "Explain this in simpler language.",
      "Show the official source.",
    ],
  };
}

function getFact(facts: MatterFact[], id: string) {
  const fact = facts.find((item) => item.id === id);
  return fact && fact.state !== "unknown" ? fact.value : undefined;
}
