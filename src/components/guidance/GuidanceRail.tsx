import Link from "next/link";
import { ArrowLeft, LockKeyhole } from "lucide-react";
import type { GuidanceResult, MatterContext } from "@/types/matter";

interface GuidanceRailProps {
  matter: MatterContext;
  guidance: GuidanceResult;
  factCount: number;
}

export function GuidanceRail({ matter, guidance, factCount }: GuidanceRailProps) {
  const sourceTypes = [...new Set(guidance.sources.map((source) => source.sourceType))];

  return (
    <aside className="space-y-5 xl:sticky xl:top-20 xl:max-h-[calc(100vh-6rem)] xl:overflow-auto">
      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">Source Coverage</p>
        <div className="mt-4 grid grid-cols-2 gap-2">
          <Metric label="Sources matched" value={String(guidance.sources.length)} />
          <Metric label="Verified facts used" value={String(factCount)} />
        </div>
        <p className="mt-3 text-sm font-semibold leading-6 text-[#6B665D]">
          Guidance is based on matched official sources and your verified context.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {sourceTypes.map((type) => (
            <span
              key={type}
              className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-2 py-1 text-[0.68rem] font-extrabold uppercase text-[#6B665D]"
            >
              {type}
            </span>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">Official Sources</p>
        <div className="mt-3 grid gap-2">
          {guidance.sources.map((source) => (
            <div key={source.id} className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-3">
              <p className="text-sm font-extrabold text-[#18150F]">{source.title}</p>
              <p className="mt-1 text-xs font-bold text-[#6B665D]">{source.sourceType}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">What is still uncertain</p>
        <div className="mt-3 grid gap-2">
          {guidance.uncertainties.map((uncertainty) => (
            <p
              key={uncertainty}
              className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-3 text-sm font-semibold leading-6 text-[#6B665D]"
            >
              {uncertainty}
            </p>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">Ask About This Guidance</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {guidance.suggestedQuestions.map((question) => (
            <button
              key={question}
              type="button"
              className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-2 text-left text-xs font-extrabold text-[#18150F] transition-colors hover:border-[#A8752B]"
            >
              {question}
            </button>
          ))}
        </div>
        <label htmlFor="guidance-question" className="sr-only">
          Ask your own question
        </label>
        <input
          id="guidance-question"
          placeholder="Ask your own question..."
          className="mt-3 min-h-11 w-full rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 text-sm font-semibold text-[#18150F] placeholder:text-[#8A8378]"
        />
      </section>

      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <div className="flex items-start gap-3">
          <LockKeyhole size={17} className="mt-0.5 text-[#071B3A]" aria-hidden="true" />
          <div>
            <p className="text-sm font-extrabold text-[#18150F]">How this guidance was created</p>
            <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">
              Verified facts from matter {matter.id.slice(0, 8)} were matched with mock official
              legal sources, then explained separately from source material.
            </p>
          </div>
        </div>
        <p className="mt-4 border-t border-[#DED7CA] pt-4 text-xs font-bold leading-5 text-[#6B665D]">
          NyayaSaarthi provides informational guidance and does not replace professional legal
          advice or an official legal determination.
        </p>
        <Link
          href="/verify"
          className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-md border border-[#DED7CA] px-3 text-sm font-extrabold text-[#071B3A] transition-colors hover:border-[#A8752B]"
        >
          <ArrowLeft size={15} aria-hidden="true" />
          Edit Situation
        </Link>
      </section>
    </aside>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-3">
      <p className="text-2xl font-extrabold text-[#18150F]">{value}</p>
      <p className="mt-1 text-[0.68rem] font-extrabold uppercase text-[#6B665D]">{label}</p>
    </div>
  );
}
