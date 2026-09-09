import type { MatterContext, MatterFact } from "@/types/matter";

interface SituationSnapshotProps {
  matter: MatterContext;
  facts: MatterFact[];
}

const preferredOrder = [
  "vehicle_type",
  "speed",
  "location",
  "road_type",
  "police_stop",
  "challan_status",
];

export function SituationSnapshot({ matter, facts }: SituationSnapshotProps) {
  const visibleFacts = [...facts]
    .filter((fact) => preferredOrder.includes(fact.id))
    .sort((a, b) => preferredOrder.indexOf(a.id) - preferredOrder.indexOf(b.id));

  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">Situation Used for Guidance</p>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <SnapshotItem label="Issue" value={matter.intent.label} />
        {visibleFacts.map((fact) => (
          <SnapshotItem key={fact.id} label={fact.label} value={fact.value} />
        ))}
      </div>
    </section>
  );
}

function SnapshotItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-3">
      <p className="text-xs font-extrabold uppercase text-[#6B665D]">{label}</p>
      <p className="mt-1 text-sm font-extrabold text-[#18150F]">{value}</p>
    </div>
  );
}
