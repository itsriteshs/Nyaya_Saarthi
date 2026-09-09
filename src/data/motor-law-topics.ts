import type { MotorLawTopic } from "@/types/nlp";

export const motorLawTopics: MotorLawTopic[] = [
  {
    id: "traffic",
    label: "Traffic",
    placeholder: "Example: I was doing 120 on the expressway. Can I be fined?",
    example: "I was doing 120 on the Bengaluru-Mysuru Expressway.",
  },
  {
    id: "challan",
    label: "Challan",
    placeholder: "Example: I got a challan but the location looks wrong.",
    example: "I got a challan but I think the recorded location is wrong.",
  },
  {
    id: "licence",
    label: "Licence",
    placeholder: "Example: Police took my driving licence after a stop.",
    example: "Traffic police took my driving licence and gave no written notice.",
  },
  {
    id: "registration",
    label: "Registration / RC",
    placeholder: "Example: RC is still in the previous owner's name.",
    example: "I bought a second-hand bike but the RC is still in the previous owner's name.",
  },
  {
    id: "insurance",
    label: "Insurance",
    placeholder: "Example: My vehicle insurance expired yesterday.",
    example: "My car insurance expired yesterday. Can I still drive today?",
  },
  {
    id: "accident",
    label: "Accident",
    placeholder: "Example: Someone hit my car and left.",
    example: "Someone hit my car near Coimbatore and left without sharing details.",
  },
];
