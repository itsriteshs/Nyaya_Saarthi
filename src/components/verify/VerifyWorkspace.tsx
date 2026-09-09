"use client";

import { useRouter } from "next/navigation";
import { AppSidebar } from "@/components/understand/AppSidebar";
import { UnderstandHeader } from "@/components/understand/UnderstandHeader";
import { SituationSummary } from "@/components/verify/SituationSummary";
import { StructuredContext } from "@/components/verify/StructuredContext";
import { VerificationRail } from "@/components/verify/VerificationRail";
import { Button } from "@/components/ui/Button";
import { confirmFact, getReadiness, updateFactValue, verifyMatter } from "@/lib/mock-context-engine";
import { useMatter } from "@/providers/MatterProvider";

export function VerifyWorkspace() {
  const router = useRouter();
  const { matter, setMatter } = useMatter();

  if (!matter) {
    return (
      <main className="grid min-h-screen place-items-center bg-[#F7F3EA] px-5 text-[#18150F]">
        <section className="max-w-xl rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-6">
          <p className="text-sm font-extrabold uppercase text-[#A8752B]">No situation ready</p>
          <h1 className="font-editorial mt-3 text-4xl font-bold text-[#071B3A]">
            No situation is currently ready for review.
          </h1>
          <p className="mt-3 text-sm font-semibold leading-6 text-[#6B665D]">
            Start from the intake page so NyayaSaarthi can build the matter context first.
          </p>
          <Button className="mt-5" onClick={() => router.push("/")}>
            Start a Situation
          </Button>
        </section>
      </main>
    );
  }

  const readiness = getReadiness(matter);
  const needsConfirmation = matter.facts.filter(
    (fact) => fact.requiresConfirmation || fact.state === "unknown",
  );
  const canCheckLaw =
    matter.missingSlots.length === 0 &&
    needsConfirmation.length === 0 &&
    matter.facts.every((fact) => fact.state !== "unknown");

  function handleConfirmFact(factId: string) {
    if (!matter) {
      return;
    }

    setMatter(confirmFact(matter, factId));
  }

  function handleChangeFact(factId: string, value: string) {
    if (!matter) {
      return;
    }

    setMatter(updateFactValue(matter, factId, value));
  }

  function handleVerify() {
    if (!matter || !canCheckLaw) {
      return;
    }

    setMatter(verifyMatter(matter));
    router.push("/guidance");
  }

  return (
    <div className="min-h-screen bg-[#F7F3EA] text-[#18150F] lg:grid lg:grid-cols-[248px_1fr]">
      <AppSidebar currentStep="verify" />
      <div className="min-w-0">
        <UnderstandHeader language={matter.language} currentStep="verify" />
        <main className="px-4 py-5 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1440px]">
            <div className="mb-5 rounded-lg border border-[#DED7CA] bg-[#FBF8F1] px-5 py-5 sm:px-6">
              <span className="inline-flex rounded-md border border-[#C49A55]/60 bg-[#F4E8D3] px-3 py-1 text-xs font-extrabold uppercase text-[#7A521F]">
                Ready for Review
              </span>
              <h1 className="font-editorial mt-3 text-4xl font-bold leading-tight text-[#18150F] sm:text-5xl">
                Review Your Situation
              </h1>
              <p className="mt-3 max-w-3xl text-sm font-semibold leading-6 text-[#6B665D] sm:text-base">
                Before we check the law, please verify what NyayaSaarthi understood from your
                description and answers.
              </p>
              <div className="mt-4 rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-4 py-3">
                <p className="text-xs font-extrabold uppercase text-[#6B665D]">Original question</p>
                <p className="mt-1 text-sm font-semibold leading-6 text-[#18150F]">
                  “{matter.originalText}”
                </p>
              </div>
            </div>

            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
              <div className="space-y-5">
                <SituationSummary matter={matter} />
                <StructuredContext
                  matter={matter}
                  onConfirmFact={handleConfirmFact}
                  onChangeFact={handleChangeFact}
                />
              </div>
              <VerificationRail
                matter={matter}
                readiness={readiness}
                needsConfirmation={needsConfirmation}
                canCheckLaw={canCheckLaw}
                onConfirmFact={handleConfirmFact}
                onChangeFact={handleChangeFact}
                onVerify={handleVerify}
              />
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
