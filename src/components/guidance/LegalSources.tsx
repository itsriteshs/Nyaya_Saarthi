import { ExternalLink } from "lucide-react";
import type { LegalSource } from "@/types/matter";

interface LegalSourcesProps {
  sources: LegalSource[];
}

export function LegalSources({ sources }: LegalSourcesProps) {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">Eligible source records</p>
      {sources.length === 0 ? <p className="mt-3 text-sm font-semibold text-[#6B665D]">No legal source met the dataset review, date and jurisdiction checks for this matter.</p> : null}
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
            {source.evidenceId ? <p className="mt-2 text-xs font-bold text-[#6B665D]">Evidence: {source.evidenceId} · Dataset review: {source.reviewStatus}</p> : null}
            {source.sourceUrl ? <a href={source.sourceUrl} target="_blank" rel="noopener noreferrer" className="mt-4 inline-flex min-h-10 items-center gap-2 rounded-md border border-[#DED7CA] px-3 text-xs font-extrabold text-[#071B3A]">Open linked government page <ExternalLink size={14} aria-hidden="true" /></a> : null}
          </article>
        ))}
      </div>
    </section>
  );
}
