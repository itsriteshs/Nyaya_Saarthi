import { AlertTriangle, CheckCircle2, ListChecks, ScanText } from "lucide-react";
import { Card } from "@/components/ui/Card";
import type { MockNlpResult } from "@/types/nlp";

interface NLPPreviewProps {
  result: MockNlpResult;
}

export function NLPPreview({ result }: NLPPreviewProps) {
  const progress = Math.round((result.readiness.found / result.readiness.total) * 100);

  return (
    <Card className="relative overflow-hidden p-5 sm:p-6">
      <div className="absolute inset-x-0 top-0 h-1 bg-[#071B3A]" aria-hidden="true" />
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-editorial text-3xl font-bold leading-none text-[#071B3A]">
            What NyayaSaarthi Understands
          </p>
          <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">
            A preview of the context extracted from your description.
          </p>
        </div>
        <span className="grid size-11 shrink-0 place-items-center rounded-md border border-[#DED7CA] bg-[#F4E8D3] text-[#A8752B]">
          <ScanText size={21} aria-hidden="true" />
        </span>
      </div>

      <div className="mt-6 rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-4">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-1 text-[#647567]" size={18} aria-hidden="true" />
          <div>
            <p className="text-xs font-extrabold uppercase text-[#6B665D]">Detected Issue</p>
            <p className="mt-1 text-base font-extrabold text-[#18150F]">
              {result.detectedIssue.label}
            </p>
            <p className="mt-1 text-sm font-semibold leading-6 text-[#6B665D]">
              {result.detectedIssue.description}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-4">
        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-extrabold uppercase text-[#6B665D]">
            <ListChecks size={15} aria-hidden="true" />
            Extracted Facts
          </div>
          <div className="grid gap-2">
            {result.extractedFacts.map((fact) => (
              <div
                key={`${fact.label}-${fact.value}`}
                className="grid grid-cols-[minmax(96px,0.55fr)_1fr] gap-3 rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-2"
              >
                <span className="text-sm font-bold text-[#6B665D]">{fact.label}</span>
                <span className="text-sm font-extrabold text-[#18150F]">{fact.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center gap-2 text-xs font-extrabold uppercase text-[#6B665D]">
            <AlertTriangle size={15} aria-hidden="true" />
            Missing Information
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {result.missingInformation.slice(0, 4).map((item) => (
              <div
                key={item}
                className="rounded-md border border-[#DED7CA] bg-[#F7F3EA] px-3 py-2 text-sm font-bold text-[#4F4A42]"
              >
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 border-t border-[#DED7CA] pt-5">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-xs font-extrabold uppercase text-[#6B665D]">Context readiness</p>
            <p className="mt-1 text-lg font-extrabold text-[#18150F]">
              {result.readiness.found} of {result.readiness.total} important facts
            </p>
          </div>
          <p className="max-w-48 text-right text-sm font-bold leading-5 text-[#6B665D]">
            {result.nextQuestion}
          </p>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#E5DDCF]">
          <div
            className="h-full rounded-full bg-[#A8752B] transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {result.visibleSignals.map((signal) => (
          <span
            key={signal}
            className="rounded-md border border-[#DED7CA] bg-[#F7F3EA] px-2.5 py-1 text-xs font-extrabold text-[#6B665D]"
          >
            {signal}
          </span>
        ))}
      </div>
    </Card>
  );
}
