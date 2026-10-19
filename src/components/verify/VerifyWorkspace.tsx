"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppSidebar } from "@/components/understand/AppSidebar";
import { UnderstandHeader } from "@/components/understand/UnderstandHeader";
import { SituationSummary } from "@/components/verify/SituationSummary";
import { StructuredContext } from "@/components/verify/StructuredContext";
import { VerificationRail } from "@/components/verify/VerificationRail";
import { Button } from "@/components/ui/Button";
import { confirmFact, getReadiness, updateFactValue, verifyMatter } from "@/lib/mock-context-engine";
import { useMatter } from "@/providers/MatterProvider";
import { getMatter } from "@/lib/api/matters";
import { confirmMatterFact, editMatterFact, verifyStructuredMatter } from "@/lib/api/conversations";

export function VerifyWorkspace() {
  const router = useRouter();
  const { matter, setMatter } = useMatter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [acknowledgeUnknowns, setAcknowledgeUnknowns] = useState(false);
  const matterId = matter?.nlpAnalysis ? matter.id : null;
  useEffect(() => {
    if (!matterId) return;
    let active = true;
    getMatter(matterId).then((latest) => { if (active) setMatter(latest); })
      .catch((cause) => { if (active) setError(cause instanceof Error ? cause.message : "Could not load matter."); });
    return () => { active = false; };
  }, [matterId, setMatter]);

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

  const readiness = matter.nlpAnalysis ? {
    found: matter.contextReadiness.found, total: matter.contextReadiness.total,
    percent: matter.contextReadiness.total ? Math.min(matter.conversation?.unresolvedRequirements.length ? 99 : 100,
      Math.round(matter.contextReadiness.found / matter.contextReadiness.total * 100)) : 0,
    complete: !!matter.conversation?.reviewEligible,
  } : getReadiness(matter);
  const needsConfirmation = matter.facts.filter(
    (fact) => !matter.conversation?.unknownSlots.includes(fact.key) &&
      (fact.requiresConfirmation || fact.state === "unknown" || fact.resolutionStatus === "ambiguous"),
  );
  const canCheckLaw =
    (!matter.nlpAnalysis ? matter.missingSlots.length === 0 :
      (!!matter.conversation?.reviewEligible &&
      (!matter.conversation?.unknownSlots.length || acknowledgeUnknowns) &&
      !matter.conversation.contradictions.some((item) => !item.resolved))) &&
    needsConfirmation.length === 0 &&
    matter.facts.every((fact) => fact.state !== "unknown");

  async function handleConfirmFact(factId: string) {
    if (!matter || busy) return false;
    if (!matter.nlpAnalysis) { setMatter(confirmFact(matter, factId)); return true; }
    setBusy(true);setError("");
    try { setMatter(await confirmMatterFact(matter.id,factId,matter.revision!));return true; }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not confirm fact.");return false; }
    finally { setBusy(false); }
  }

  async function handleChangeFact(factId: string, value: string) {
    if (!matter || busy) return false;
    if (!matter.nlpAnalysis) { setMatter(updateFactValue(matter, factId, value)); return true; }
    setBusy(true);setError("");
    try { setMatter(await editMatterFact(matter.id,factId,matter.revision!,value));return true; }
    catch (cause) { setError(cause instanceof Error ? cause.message : "Could not save correction.");return false; }
    finally { setBusy(false); }
  }

  async function handleVerify() {
    if (!matter || !canCheckLaw || busy) return;
    if (!matter.nlpAnalysis) { setMatter(verifyMatter(matter));router.push("/guidance");return; }
    setBusy(true);setError("");
    try {
      const verified=await verifyStructuredMatter(matter.id,matter.revision!,acknowledgeUnknowns);
      setMatter(verified);router.push("/guidance");
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Verification was not saved."); }
    finally { setBusy(false); }
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
              {matter.nlpAnalysis ? <p className="mt-3 rounded-md border border-[#C49A55]/60 bg-[#F4E8D3] p-3 text-sm font-bold text-[#7A521F]">
                Confirmed facts are saved to this matter. Verification records your review; legal source checking is not available yet.
              </p> : null}
              {error ? <p role="alert" className="mt-3 text-sm font-bold text-red-700">{error}</p> : null}
              {matter.nlpAnalysis && matter.conversation?.unknownSlots.length ? <label className="mt-3 flex items-center gap-2 text-sm font-bold text-[#4F4A42]">
                <input type="checkbox" checked={acknowledgeUnknowns} onChange={(event) => setAcknowledgeUnknowns(event.target.checked)} />
                I acknowledge that required facts remain unknown.
              </label> : null}
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
                canCheckLaw={canCheckLaw && !busy}
                realMode={!!matter.nlpAnalysis}
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
