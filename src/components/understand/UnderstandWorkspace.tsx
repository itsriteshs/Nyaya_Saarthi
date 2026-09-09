"use client";

import { useMemo } from "react";
import { AppSidebar } from "@/components/understand/AppSidebar";
import { ContextPanel } from "@/components/understand/ContextPanel";
import { ConversationPanel } from "@/components/understand/ConversationPanel";
import { UnderstandHeader } from "@/components/understand/UnderstandHeader";
import { createMatterContext, answerCurrentQuestion, getReadiness } from "@/lib/mock-context-engine";
import { useMatter } from "@/providers/MatterProvider";
import type { LanguageOption } from "@/types/nlp";

interface UnderstandWorkspaceProps {
  initialText?: string;
  initialLanguage: LanguageOption;
}

export function UnderstandWorkspace({ initialText, initialLanguage }: UnderstandWorkspaceProps) {
  const { matter, setMatter } = useMatter();
  const fallbackMatter = useMemo(
    () => createMatterContext(initialText, initialLanguage),
    [initialText, initialLanguage],
  );
  const context = matter ?? fallbackMatter;

  const readiness = useMemo(() => getReadiness(context), [context]);

  function handleAnswer(answer: string) {
    setMatter(answerCurrentQuestion(context, answer));
  }

  return (
    <div className="min-h-screen bg-[#F7F3EA] text-[#18150F] lg:grid lg:grid-cols-[248px_1fr]">
      <AppSidebar />
      <div className="min-w-0">
        <UnderstandHeader language={context.language} currentStep="understand" />
        <main className="px-4 py-5 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1440px]">
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_410px]">
              <ConversationPanel context={context} onAnswer={handleAnswer} />
              <ContextPanel context={context} readiness={readiness} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
