import { ArrowRight } from "lucide-react";
import type { GuidanceResult } from "@/types/matter";

interface FactLawMappingProps {
  guidance: GuidanceResult;
}

export function FactLawMapping({ guidance }: FactLawMappingProps) {
  const primary = guidance.mappings[0];

  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">Why this guidance applies</p>
      <h2 className="font-editorial mt-2 text-3xl font-bold text-[#18150F]">
        Fact, official law, explanation
      </h2>

      {!primary ? <p className="mt-4 text-sm font-semibold leading-6 text-[#6B665D]">{guidance.sources.length
        ? "A reviewed provision was found, but no structured rule could be linked to all the confirmed facts. The provision may still be relevant; the uncertainties below explain what remains unresolved."
        : "No eligible reviewed source was available to connect to this situation. This is a gap in the app’s evidence, not a finding that no rule applies."}</p> : <div className="mt-5 grid gap-3 lg:grid-cols-[1fr_auto_1fr_auto_1fr] lg:items-stretch">
        <MappingPanel
          eyebrow="Your Fact"
          tone="fact"
          title={primary.fact}
          text="This comes from the situation you verified."
        />
        <Connector />
        <MappingPanel
          eyebrow="Official Law"
          tone="law"
          title={primary.sourceTitle}
          text={primary.evidenceId ? `Evidence ${primary.evidenceId}` : "Dataset source record"}
        />
        <Connector />
        <MappingPanel
          eyebrow="NyayaSaarthi Explanation"
          tone="explanation"
          title="What this may mean for you"
          text={primary.explanation}
        />
      </div>}
    </section>
  );
}

function MappingPanel({
  eyebrow,
  title,
  text,
  tone,
}: {
  eyebrow: string;
  title: string;
  text: string;
  tone: "fact" | "law" | "explanation";
}) {
  const tones = {
    fact: "bg-[#F4F7F0]",
    law: "bg-[#EEF2F5]",
    explanation: "bg-[#F4E8D3]",
  };

  return (
    <article className={`rounded-md border border-[#DED7CA] ${tones[tone]} p-4`}>
      <p className="text-xs font-extrabold uppercase text-[#6B665D]">{eyebrow}</p>
      <h3 className="mt-2 text-base font-extrabold leading-6 text-[#18150F]">{title}</h3>
      <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">{text}</p>
    </article>
  );
}

function Connector() {
  return (
    <div className="grid place-items-center text-[#A8752B]" aria-hidden="true">
      <ArrowRight className="hidden lg:block" size={20} />
      <span className="block h-5 w-px bg-[#DED7CA] lg:hidden" />
    </div>
  );
}
