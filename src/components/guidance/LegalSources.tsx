import { ExternalLink } from "lucide-react";
import type { LegalSource } from "@/types/matter";

interface LegalSourcesProps {
  sources: LegalSource[];
}

export function LegalSources({ sources }: LegalSourcesProps) {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">Relevant Official Sources</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {sources.map((source) => (
          <article key={source.id} className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-base font-extrabold text-[#18150F]">{source.title}</h3>
                <p className="mt-1 text-sm font-bold text-[#6B665D]">{source.authority}</p>
              </div>
              <span className="rounded-md border border-[#DED7CA] bg-[#F7F3EA] px-2 py-1 text-[0.68rem] font-extrabold uppercase text-[#6B665D]">
                {source.sourceType}
              </span>
            </div>
            {source.provision ? (
              <p className="mt-3 text-sm font-semibold text-[#18150F]">
                Provision: <span className="text-[#6B665D]">{source.provision}</span>
              </p>
            ) : null}
            <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">
              {source.relevantPoint}
            </p>
            <button
              type="button"
              disabled
              className="mt-4 inline-flex min-h-10 cursor-not-allowed items-center gap-2 rounded-md border border-[#DED7CA] bg-[#F7F3EA] px-3 text-xs font-extrabold text-[#6B665D]"
            >
              Source link will come from retrieval API
              <ExternalLink size={14} aria-hidden="true" />
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
