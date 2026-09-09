import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { ClarificationQuestion } from "@/components/understand/ClarificationQuestion";
import { ConversationMessage } from "@/components/understand/ConversationMessage";
import { MessageComposer } from "@/components/understand/MessageComposer";
import type { MatterContext } from "@/types/matter";

interface ConversationPanelProps {
  context: MatterContext;
  onAnswer: (answer: string) => void;
}

export function ConversationPanel({ context, onAnswer }: ConversationPanelProps) {
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

        <div className="space-y-4 px-4 py-5 sm:px-6">
          {context.messages.map((message) => (
            <ConversationMessage key={message.id} message={message} />
          ))}

          {context.currentQuestion ? (
            <ClarificationQuestion question={context.currentQuestion} onAnswer={onAnswer} />
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
                className="mt-5 inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-[#071B3A] bg-[#071B3A] px-4 text-sm font-extrabold text-white transition-colors hover:border-[#102A52] hover:bg-[#102A52]"
              >
                Review My Situation
                <ArrowRight size={16} aria-hidden="true" />
              </Link>
            </div>
          )}
        </div>

        {context.currentQuestion ? (
          <MessageComposer
            disabled={context.currentQuestion.type !== "text"}
            onSend={onAnswer}
          />
        ) : null}
      </div>
    </section>
  );
}
