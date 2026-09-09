import { UnderstandWorkspace } from "@/components/understand/UnderstandWorkspace";
import type { LanguageOption } from "@/types/nlp";

interface UnderstandPageProps {
  searchParams: Promise<{
    text?: string;
    language?: string;
  }>;
}

export default async function UnderstandPage({ searchParams }: UnderstandPageProps) {
  const params = await searchParams;
  const initialLanguage = isLanguageOption(params.language) ? params.language : "english";

  return <UnderstandWorkspace initialText={params.text} initialLanguage={initialLanguage} />;
}

function isLanguageOption(value: string | undefined): value is LanguageOption {
  return value === "auto" || value === "english" || value === "hindi" || value === "hinglish";
}
