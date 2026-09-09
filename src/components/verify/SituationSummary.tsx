import Link from "next/link";
import { ArrowLeft, ArrowRight } from "lucide-react";
import type { MatterContext } from "@/types/matter";

interface SituationSummaryProps {
  matter: MatterContext;
}

export function SituationSummary({ matter }: SituationSummaryProps) {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">Here&apos;s what we understood</p>
      <p className="font-editorial mt-3 max-w-4xl text-3xl font-bold leading-tight text-[#18150F]">
        {buildSummary(matter)}
      </p>
      <div className="mt-5 flex flex-wrap gap-3 border-t border-[#DED7CA] pt-5">
        <Link
          href="/understand"
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-[#DED7CA] bg-[#FBF8F1] px-4 text-sm font-extrabold text-[#071B3A] transition-colors hover:border-[#A8752B]"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          Back to Clarification
        </Link>
        <a
          href="#verification-actions"
          className="inline-flex min-h-11 items-center justify-center gap-2 rounded-md border border-[#071B3A] bg-[#071B3A] px-4 text-sm font-extrabold text-white transition-colors hover:bg-[#102A52]"
        >
          Review Confirmation
          <ArrowRight size={16} aria-hidden="true" />
        </a>
      </div>
    </section>
  );
}

function buildSummary(matter: MatterContext) {
  const fact = (id: string) => matter.facts.find((item) => item.id === id)?.value;
  const vehicle = fact("vehicle_type");
  const speed = fact("speed");
  const location = fact("location");
  const police = fact("police_stop");
  const challan = fact("challan_status");

  const driving = [
    vehicle && vehicle !== "Not answered yet" ? `driving a ${vehicle.toLowerCase()}` : "driving",
    speed && speed !== "Not answered yet" ? `at approximately ${speed}` : null,
    location && location !== "Not answered yet" ? `on the ${location}` : null,
  ]
    .filter(Boolean)
    .join(" ");

  const enforcement =
    police === "Stopped by police" && challan === "None reported"
      ? "Police stopped you, and no challan has been reported."
      : police && police !== "Not answered yet"
        ? `${police}.`
        : "Police or challan status has not been fully established.";

  return `You reported ${driving}. ${enforcement}`;
}
