import type { ExamplePrompt } from "@/types/nlp";

export const defaultSituation =
  "I was doing 120 on the Bengaluru-Mysuru Expressway.";

export const examplePrompts: ExamplePrompt[] = [
  {
    id: "speeding",
    text: "I was doing 120. Can I be fined?",
  },
  {
    id: "licence",
    text: "Police took my licence. Can they do that?",
  },
  {
    id: "challan",
    text: "I got a challan but I think it is wrong.",
  },
  {
    id: "hit-run",
    text: "Someone hit my car and left.",
  },
  {
    id: "insurance",
    text: "My insurance expired yesterday. Can I drive?",
  },
  {
    id: "rc-transfer",
    text: "RC is still in the previous owner's name.",
  },
];
