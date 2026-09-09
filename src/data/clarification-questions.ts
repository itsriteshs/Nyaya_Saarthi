import type { ClarificationQuestion, MatterSlot } from "@/types/matter";

export const clarificationQuestions: Record<MatterSlot, ClarificationQuestion> = {
  vehicle_type: {
    slot: "vehicle_type",
    question: "What type of vehicle were you driving?",
    type: "options",
    options: [
      { label: "Private car", value: "Private car" },
      { label: "Motorcycle", value: "Motorcycle" },
      { label: "Commercial vehicle", value: "Commercial vehicle" },
      { label: "Other", value: "Other vehicle" },
    ],
    why: "Vehicle category may affect which Motor Vehicle rules are relevant.",
  },
  location: {
    slot: "location",
    question: "Where did this happen?",
    type: "text",
    why: "Road context can matter because restrictions may depend on the location and road segment.",
  },
  enforcement_status: {
    slot: "enforcement_status",
    question: "Were you stopped by police or did you receive a challan, receipt or notice?",
    type: "options",
    options: [
      { label: "Stopped by police", value: "Stopped by police" },
      { label: "Stopped, no challan", value: "Stopped by police, no challan" },
      { label: "Received challan", value: "Received challan" },
      { label: "Both", value: "Stopped by police and received challan" },
      { label: "Neither", value: "Neither reported" },
      { label: "Not sure", value: "Not sure" },
    ],
    why: "The next page can review your situation more clearly if enforcement status is separated from the original question.",
  },
  licence_action: {
    slot: "licence_action",
    question: "When you say they 'took' your licence, what happened?",
    type: "options",
    options: [
      { label: "They only inspected it", value: "Licence inspected only" },
      { label: "They kept the physical licence", value: "Physical licence kept" },
      { label: "They formally seized or impounded it", value: "Licence seized or impounded" },
      { label: "I'm not sure", value: "Not sure" },
    ],
    why: "The word 'took' can describe inspection, temporary holding or a formal seizure.",
  },
};
