import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ClarificationQuestion } from "@/components/understand/ClarificationQuestion";
import { ConversationMessage } from "@/components/understand/ConversationMessage";
import { MessageComposer } from "@/components/understand/MessageComposer";
import type { MatterContext } from "@/types/matter";

interface ConversationPanelProps {
  context: MatterContext;
  onAnswer: (answer: string) => Promise<boolean> | void;
  busy?: boolean;
  error?: string;
}

export function ConversationPanel({ context, onAnswer, busy = false, error = "" }: ConversationPanelProps) {
  return (
    <section className="min-w-0">
      <div className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1]">
        <div className="border-b border-[#DED7CA] px-5 py-5 sm:px-6">
          <span className="inline-flex rounded-md border border-[#C49A55]/60 bg-[#F4E8D3] px-3 py-1 text-xs font-extrabold uppercase text-[#7A521F]">
            Understanding Context
          </span>
          <h1 className="font-editorial mt-3 text-4xl font-bold leading-tight text-[#18150F] sm:text-5xl">
            Understand Your Situation
          </h1>
          <p className="mt-3 max-w-3xl text-sm font-semibold leading-6 text-[#6B665D] sm:text-base">
            Tell us what happened in your own words. NyayaSaarthi will identify the important
            details and ask only what is still needed.
          </p>
        </div>

        {context.conversation?.urgentAssistance ? (
          <div role="alert" className="mx-4 mt-4 rounded-md border border-red-400 bg-red-50 p-4 text-base font-bold leading-7 text-red-900">
            {context.messages.find((message) => message.id === "urgent-assistance")?.text}
          </div>
        ) : null}
        <div className="space-y-4 px-4 py-5 sm:px-6">
          {context.messages.map((message) => (
            <ConversationMessage key={message.id} message={message} />
          ))}
          {error ? <p role="alert" className="rounded-md border border-red-300 p-3 text-sm font-bold text-red-700">{error}</p> : null}

          {context.nlpAnalysis && context.currentQuestion ? (
            <>
              <ClarificationQuestion question={context.currentQuestion} onAnswer={onAnswer} busy={busy} />
              <button type="button" disabled={busy} onClick={() => onAnswer("I don't know")}
                className="text-sm font-bold text-[#7A521F] underline disabled:opacity-50">I don&apos;t know / Skip with uncertainty</button>
            </>
          ) : context.nlpAnalysis ? (
            <div className="rounded-lg border border-[#C49A55]/60 bg-[#F4E8D3] p-5">
              <p className="text-sm font-extrabold uppercase text-[#7A521F]">{context.nlpAnalysis.intent.scoreType.startsWith("User-selected") ? "Issue selected by you" : "Model suggestion"}</p>
              <h2 className="font-editorial mt-2 text-3xl font-bold text-[#18150F]">
                {context.conversation?.reviewEligible ? "Review the extracted context" : "More context or confirmation is needed"}
              </h2>
              <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">
                {context.currentQuestion?.question ??
                  (context.nlpAnalysis.intent.needsClarification
                    ? "The intent is uncertain. Review the alternatives and extracted facts."
                    : "Confirm each extracted fact before relying on it.")}
              </p>
              {context.nlpAnalysis.unresolvedSlots.length ? <p className="mt-2 text-sm font-semibold text-[#7A521F]">
                {context.nlpAnalysis.unresolvedSlots.length} conditional requirement(s) could not be resolved.
              </p> : null}
              {context.conversation?.reviewEligible ? <Link href="/verify" className="mt-5 inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-[#071B3A] bg-[#071B3A] px-4 text-sm font-extrabold !text-white">
                Review My Situation <ArrowRight size={16} aria-hidden="true" />
              </Link> : null}
            </div>
          ) : context.currentQuestion ? (
            <ClarificationQuestion question={context.currentQuestion} onAnswer={onAnswer} busy={busy} />
          ) : (
            <div className="rounded-lg border border-[#C49A55]/60 bg-[#F4E8D3] p-5">
              <p className="text-sm font-extrabold uppercase text-[#7A521F]">
                Your situation is ready to review.
              </p>
              <h2 className="font-editorial mt-2 text-3xl font-bold text-[#18150F]">
                Enough context has been established
              </h2>
              <p className="mt-2 max-w-2xl text-sm font-semibold leading-6 text-[#6B665D]">
                We have enough context to show you what NyayaSaarthi understood before checking the
                law.
              </p>
              <Link
                href="/verify"
                className="mt-5 inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-[#071B3A] bg-[#071B3A] px-4 text-sm font-extrabold !text-white transition-colors hover:border-[#102A52] hover:bg-[#102A52]"
              >
                Review My Situation
                <ArrowRight size={16} aria-hidden="true" />
              </Link>
            </div>
          )}
        </div>

        {context.currentQuestion ? (
          <MessageComposer
            disabled={busy || context.currentQuestion.type !== "text"}
            onSend={onAnswer}
          />
        ) : null}
      </div>
    </section>
  );
}
