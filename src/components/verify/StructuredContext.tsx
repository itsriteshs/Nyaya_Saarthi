import { FactReviewRow } from "@/components/verify/FactReviewRow";
import type { MatterContext } from "@/types/matter";

interface StructuredContextProps {
  matter: MatterContext;
  onConfirmFact: (factId: string) => void;
  onChangeFact: (factId: string, value: string) => void;
}

export function StructuredContext({ matter, onConfirmFact, onChangeFact }: StructuredContextProps) {
  const factGroups = [
    {
      title: "Issue",
      facts: [{ id: "intent", label: "Detected issue", value: matter.intent.label }],
    },
    {
      title: "Vehicle",
      facts: matter.facts.filter((fact) => fact.id === "vehicle_type"),
    },
    {
      title: "Road & Location",
      facts: matter.facts.filter((fact) => fact.id === "location" || fact.id === "road_type"),
    },
    {
      title: "Driving Context",
      facts: matter.facts.filter((fact) => fact.id === "speed"),
    },
    {
      title: "Enforcement",
      facts: matter.facts.filter((fact) => fact.id === "police_stop" || fact.id === "challan_status"),
    },
  ];

  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <div>
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">Structured Situation</p>
        <h2 className="font-editorial mt-2 text-3xl font-bold text-[#18150F]">
          Human-readable meaning representation
        </h2>
      </div>

      <div className="mt-5 grid gap-4">
        {factGroups.map((group) => (
          <section key={group.title} className="border-t border-[#DED7CA] pt-4">
            <h3 className="text-xs font-extrabold uppercase text-[#6B665D]">{group.title}</h3>
            <div className="mt-3 grid gap-2">
              {group.facts.length > 0 ? (
                group.facts.map((fact) =>
                  "provenance" in fact ? (
                    <FactReviewRow
                      key={fact.id}
                      fact={fact}
                      onConfirm={onConfirmFact}
                      onChange={onChangeFact}
                    />
                  ) : (
                    <div
                      key={fact.id}
                      className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-3"
                    >
                      <p className="text-sm font-bold text-[#6B665D]">{fact.label}</p>
                      <p className="mt-1 text-sm font-extrabold text-[#18150F]">{fact.value}</p>
                    </div>
                  ),
                )
              ) : (
                <div className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-3 text-sm font-bold text-[#6B665D]">
                  Not established
                </div>
              )}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}
