import { cn } from "@/lib/utils";
import type { MatterFact } from "@/types/matter";

interface ContextFactRowProps {
  fact: MatterFact;
}

const stateLabel = {
  provided: "Provided",
  confirmed: "Confirmed",
  inferred: "Inferred",
  unknown: "Unknown",
};

export function ContextFactRow({ fact }: ContextFactRowProps) {
  return (
    <div className="grid grid-cols-[1fr_auto] gap-3 rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-3">
      <div>
        <p className="text-sm font-bold text-[#6B665D]">{fact.label}</p>
        <p className="mt-1 text-sm font-extrabold text-[#18150F]">{fact.value}</p>
      </div>
      <span
        className={cn(
          "h-fit rounded-md border px-2 py-1 text-[0.68rem] font-extrabold uppercase",
          fact.state === "unknown"
            ? "border-[#DED7CA] bg-[#F7F3EA] text-[#6B665D]"
            : "border-[#C49A55]/60 bg-[#F4E8D3] text-[#7A521F]",
        )}
      >
        {stateLabel[fact.state]}
      </span>
    </div>
  );
}
