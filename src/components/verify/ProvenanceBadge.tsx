import { cn } from "@/lib/utils";
import type { FactProvenance } from "@/types/matter";

interface ProvenanceBadgeProps {
  provenance: FactProvenance;
}

const labels: Record<FactProvenance, string> = {
  USER_PROVIDED: "You said this",
  USER_CONFIRMED: "You confirmed this",
  SYSTEM_INFERRED: "NyayaSaarthi inferred this",
  UNKNOWN: "Not established",
};

export function ProvenanceBadge({ provenance }: ProvenanceBadgeProps) {
  return (
    <span
      className={cn(
        "h-fit rounded-md border px-2 py-1 text-[0.68rem] font-extrabold uppercase",
        provenance === "SYSTEM_INFERRED" && "border-[#C49A55]/70 bg-[#F4E8D3] text-[#7A521F]",
        provenance === "USER_CONFIRMED" && "border-[#A8BEA7] bg-[#EEF5ED] text-[#35533A]",
        provenance === "USER_PROVIDED" && "border-[#C9D2DD] bg-[#EEF2F5] text-[#071B3A]",
        provenance === "UNKNOWN" && "border-[#DED7CA] bg-[#F7F3EA] text-[#6B665D]",
      )}
    >
      {labels[provenance]}
    </span>
  );
}
