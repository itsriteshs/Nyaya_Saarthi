import Link from "next/link";
import { ArrowLeft, ArrowRight, CheckCircle2, LockKeyhole } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { FactReviewRow } from "@/components/verify/FactReviewRow";
import type { MatterContext, MatterFact } from "@/types/matter";

interface VerificationRailProps {
  matter: MatterContext;
  readiness: {
    found: number;
    total: number;
    percent: number;
  };
  needsConfirmation: MatterFact[];
  canCheckLaw: boolean;
  onConfirmFact: (factId: string) => void;
  onChangeFact: (factId: string, value: string) => void;
  onVerify: () => void;
}

export function VerificationRail({
  readiness,
  needsConfirmation,
  canCheckLaw,
  onConfirmFact,
  onChangeFact,
  onVerify,
}: VerificationRailProps) {
  return (
    <aside className="space-y-5 xl:sticky xl:top-20 xl:max-h-[calc(100vh-6rem)] xl:overflow-auto">
      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">Legal Context Completeness</p>
        <p className="mt-2 text-2xl font-extrabold text-[#18150F]">
          {readiness.found} / {readiness.total}
        </p>
        <p className="mt-1 text-sm font-semibold leading-6 text-[#6B665D]">
          {needsConfirmation.length > 0
            ? "One detail still needs confirmation before legal retrieval."
            : "All required context is ready for verification."}
        </p>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-[#E5DDCF]">
          <div
            className="h-full rounded-full bg-[#A8752B] transition-all"
            style={{ width: `${readiness.percent}%` }}
          />
        </div>
      </section>

      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">Needs Confirmation</p>
        <div className="mt-3 grid gap-2">
          {needsConfirmation.length > 0 ? (
            needsConfirmation.map((fact) => (
              <FactReviewRow
                key={fact.id}
                fact={fact}
                onConfirm={onConfirmFact}
                onChange={onChangeFact}
              />
            ))
          ) : (
            <div className="flex items-center gap-2 rounded-md border border-[#A8BEA7] bg-[#EEF5ED] px-3 py-3 text-sm font-extrabold text-[#35533A]">
              <CheckCircle2 size={16} aria-hidden="true" />
              All required context is ready for verification.
            </div>
          )}
        </div>
      </section>

      <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <p className="text-xs font-extrabold uppercase text-[#A8752B]">Why verification matters</p>
        <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">
          Motor Vehicle rules can depend on details such as vehicle category, location, road
          context and enforcement status. Confirming the situation helps prevent retrieval for the
          wrong circumstances.
        </p>
        <div className="mt-4 rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-3">
          <div className="flex items-start gap-2">
            <LockKeyhole size={16} className="mt-0.5 text-[#071B3A]" aria-hidden="true" />
            <div>
              <p className="text-sm font-extrabold text-[#18150F]">Legal retrieval: Not started</p>
              <p className="mt-1 text-xs font-bold text-[#6B665D]">
                Waiting for your verification
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="verification-actions" className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5">
        <Button className="w-full" disabled={!canCheckLaw} onClick={onVerify}>
          Confirm & Check Law
          <ArrowRight size={16} aria-hidden="true" />
        </Button>
        {!canCheckLaw ? (
          <p className="mt-2 text-xs font-bold text-[#6B665D]">
            Confirm the remaining detail before checking the law.
          </p>
        ) : null}
        <Link
          href="/understand"
          className="mt-3 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-md border border-[#DED7CA] px-4 text-sm font-extrabold text-[#071B3A] transition-colors hover:border-[#A8752B]"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          Back to Clarification
        </Link>
      </section>
    </aside>
  );
}
