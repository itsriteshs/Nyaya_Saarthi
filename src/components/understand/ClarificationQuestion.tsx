import { HelpCircle } from "lucide-react";
import type { ClarificationQuestion as ClarificationQuestionType } from "@/types/matter";

interface ClarificationQuestionProps {
  question: ClarificationQuestionType;
  onAnswer: (answer: string) => void;
}

export function ClarificationQuestion({ question, onAnswer }: ClarificationQuestionProps) {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FFFDF8] p-5">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">We need one more detail</p>
      <h2 className="mt-2 text-xl font-extrabold leading-7 text-[#18150F]">{question.question}</h2>

      {question.type === "options" ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {question.options?.map((option) => (
            <button
              key={option.value}
              type="button"
              className="min-h-11 rounded-md border border-[#DED7CA] bg-[#F7F3EA] px-4 text-sm font-extrabold text-[#18150F] transition-colors hover:border-[#A8752B] hover:bg-[#F4E8D3]"
              onClick={() => onAnswer(option.value)}
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : (
        <p className="mt-4 rounded-md border border-[#DED7CA] bg-[#F7F3EA] px-4 py-3 text-sm font-semibold text-[#6B665D]">
          Type your answer in the composer below.
        </p>
      )}

      <div className="mt-5 flex gap-3 border-t border-[#DED7CA] pt-4">
        <HelpCircle className="mt-0.5 shrink-0 text-[#A8752B]" size={18} aria-hidden="true" />
        <div>
          <p className="text-sm font-extrabold text-[#18150F]">Why we are asking</p>
          <p className="mt-1 text-sm font-semibold leading-6 text-[#6B665D]">{question.why}</p>
        </div>
      </div>
    </section>
  );
}
