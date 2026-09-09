import { defaultSituation } from "@/data/examples";
import type { LanguageOption } from "@/types/nlp";

export const defaultMatter = {
  originalText: defaultSituation.replace(" on the Bengaluru-Mysuru Expressway", ""),
  language: "english" as LanguageOption,
};
