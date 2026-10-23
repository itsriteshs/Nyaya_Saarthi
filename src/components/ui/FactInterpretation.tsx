import type { MatterFact } from "@/types/matter";

export function FactInterpretation({ fact }: { fact: MatterFact }) {
  return <div className="mt-1 break-words text-xs leading-5 text-[#6B665D]">
    {fact.normalizedValue ? <p>Interpreted as: {fact.normalizedValue}{fact.unit && fact.unit !== "unknown" ? ` ${fact.unit}` : ""}</p> : null}
    {fact.interpretationNotes?.map((note, index) => <p className="font-semibold" key={index}>{note}</p>)}
  </div>;
}
