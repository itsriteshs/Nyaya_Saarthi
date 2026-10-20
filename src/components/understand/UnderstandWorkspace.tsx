"use client";

import { useEffect, useMemo, useState } from "react";
import { AppSidebar } from "@/components/understand/AppSidebar";
import { ContextPanel } from "@/components/understand/ContextPanel";
import { ConversationPanel } from "@/components/understand/ConversationPanel";
import { UnderstandHeader } from "@/components/understand/UnderstandHeader";
import { createMatterContext, answerCurrentQuestion, getReadiness } from "@/lib/mock-context-engine";
import { useMatter } from "@/providers/MatterProvider";
import { getMatter } from "@/lib/api/matters";
import { submitAnswer } from "@/lib/api/conversations";
import { ApiError } from "@/lib/api/client";
import type { LanguageOption } from "@/types/nlp";

interface UnderstandWorkspaceProps {
  initialText?: string;
  initialLanguage: LanguageOption;
}

export function UnderstandWorkspace({ initialText, initialLanguage }: UnderstandWorkspaceProps) {
  const { matter, restored, setMatter } = useMatter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const demoMode = process.env.NEXT_PUBLIC_NYAYA_DEMO_MODE === "true";
  const matterId = matter?.nlpAnalysis ? matter.id : null;
  useEffect(() => {
    if (!matterId) return;
    let active = true;
    getMatter(matterId).then((latest) => { if (active) setMatter(latest); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : "Could not load matter."); });
    return () => { active = false; };
  }, [matterId, setMatter]);
  const fallbackMatter = useMemo(
    () => demoMode && restored ? createMatterContext(initialText, initialLanguage) : null,
    [demoMode, restored, initialText, initialLanguage],
  );
  const context = matter ?? (demoMode ? fallbackMatter : null);

  const readiness = useMemo(() => context?.nlpAnalysis ? {
    found: context.contextReadiness.found,
    total: context.contextReadiness.total,
    percent: context.contextReadiness.total ? Math.min(context.conversation?.unresolvedRequirements.length ? 99 : 100,
      Math.round(context.contextReadiness.found / context.contextReadiness.total * 100)) : 0,
    complete: !!context.conversation?.reviewEligible,
  } : context ? getReadiness(context) : { found: 0, total: 0, percent: 0, complete: false }, [context]);

  async function handleAnswer(answer: string) {
    if (!context || busy) return false;
    if (!context.nlpAnalysis) { setMatter(answerCurrentQuestion(context, answer)); return true; }
    if (!context.currentQuestion?.id || !context.revision) return false;
    setBusy(true);setError("");
    try {
      const updated = await submitAnswer(context.id,context.revision,context.currentQuestion.id,answer,crypto.randomUUID());
      setMatter(updated);
      return true;
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save answer.");
      if (cause instanceof ApiError && cause.status === 409) {
        try { setMatter(await getMatter(context.id)); } catch { /* Retain the saved view. */ }
      }
      return false;
    } finally { setBusy(false); }
  }

  if (!context) return <main className="grid min-h-screen place-items-center bg-[#F7F3EA] p-6 text-[#18150F]">
    <p className="text-lg font-bold">Start a situation on the Home page to create a matter.</p>
  </main>;

  return (
    <div className="min-h-screen bg-[#F7F3EA] text-[#18150F] lg:grid lg:grid-cols-[248px_1fr]">
      <AppSidebar />
      <div className="min-w-0">
        <UnderstandHeader language={context.language} currentStep="understand" />
        <main className="px-4 py-5 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1440px]">
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_410px]">
              <ConversationPanel context={context} onAnswer={handleAnswer} busy={busy} error={error} />
              <ContextPanel context={context} readiness={readiness} />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
