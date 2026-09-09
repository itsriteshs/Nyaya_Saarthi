import { AlertCircle, CheckCircle2, CircleHelp, FileQuestion } from "lucide-react";
import { ContextFactRow } from "@/components/understand/ContextFactRow";
import { ContextReadiness } from "@/components/understand/ContextReadiness";
import type { MatterContext } from "@/types/matter";

interface ContextPanelProps {
  context: MatterContext;
  readiness: {
    found: number;
    total: number;
    percent: number;
    complete: boolean;
  };
}

export function ContextPanel({ context, readiness }: ContextPanelProps) {
  return (
    <aside className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 xl:sticky xl:top-20 xl:max-h-[calc(100vh-6rem)] xl:overflow-auto">
      <div>
        <p className="font-editorial text-3xl font-bold leading-none text-[#071B3A]">
          What NyayaSaarthi Understands
        </p>
        <p className="mt-2 text-sm font-semibold text-[#6B665D]">Updated as you answer.</p>
      </div>

      <section className="mt-5 rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-4">
        <div className="flex items-start gap-3">
          <CheckCircle2 className="mt-1 text-[#647567]" size={18} aria-hidden="true" />
          <div>
            <p className="text-xs font-extrabold uppercase text-[#6B665D]">Detected Issue</p>
            <p className="mt-1 text-base font-extrabold text-[#18150F]">{context.intent.label}</p>
            <p className="mt-1 text-xs font-extrabold uppercase text-[#A8752B]">
              {context.intent.descriptor}
            </p>
          </div>
        </div>
      </section>

      <section className="mt-5">
        <h2 className="text-xs font-extrabold uppercase text-[#6B665D]">Extracted Facts</h2>
        <div className="mt-2 grid gap-2">
          {context.facts.map((fact) => (
            <ContextFactRow key={fact.id} fact={fact} />
          ))}
        </div>
      </section>

      <section className="mt-5">
        <h2 className="text-xs font-extrabold uppercase text-[#6B665D]">Still Needed</h2>
        <div className="mt-2 grid gap-2">
          {context.missingSlots.length > 0 ? (
            context.missingSlots.map((slot) => (
              <div
                key={slot}
                className="flex items-center gap-2 rounded-md border border-[#DED7CA] bg-[#F7F3EA] px-3 py-2 text-sm font-bold text-[#4F4A42]"
              >
                <AlertCircle size={15} className="text-[#A8752B]" aria-hidden="true" />
                {formatSlot(slot)}
              </div>
            ))
          ) : (
            <div className="flex items-center gap-2 rounded-md border border-[#C49A55]/60 bg-[#F4E8D3] px-3 py-2 text-sm font-extrabold text-[#18150F]">
              <CheckCircle2 size={15} className="text-[#647567]" aria-hidden="true" />
              Ready for review
            </div>
          )}
        </div>
      </section>

      <section className="mt-5 rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-4">
        <div className="flex gap-3">
          <CircleHelp size={17} className="mt-0.5 shrink-0 text-[#A8752B]" aria-hidden="true" />
          <div>
            <h2 className="text-sm font-extrabold text-[#18150F]">Why we are asking</h2>
            <p className="mt-1 text-sm font-semibold leading-6 text-[#6B665D]">
              {context.currentQuestion?.why ??
                "Legal applicability will be checked only after you verify the structured context."}
            </p>
          </div>
        </div>
      </section>

      <ContextReadiness readiness={readiness} />

      <section className="mt-5 rounded-md border border-[#DED7CA] bg-[#F7F3EA] p-4">
        <div className="flex gap-3">
          <FileQuestion size={17} className="mt-0.5 shrink-0 text-[#071B3A]" aria-hidden="true" />
          <div>
            <h2 className="text-sm font-extrabold text-[#18150F]">Next question</h2>
            <p className="mt-1 text-sm font-semibold leading-6 text-[#6B665D]">
              {context.currentQuestion?.question ?? "Review the understood situation."}
            </p>
          </div>
        </div>
      </section>
    </aside>
  );
}

function formatSlot(slot: string) {
  const labels: Record<string, string> = {
    vehicle_type: "Vehicle type",
    location: "Location / road context",
    enforcement_status: "Police / challan status",
    licence_action: "Meaning of licence action",
  };

  return labels[slot] ?? slot;
}
