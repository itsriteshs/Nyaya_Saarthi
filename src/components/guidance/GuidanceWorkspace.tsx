"use client";

import { useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { AppSidebar } from "@/components/understand/AppSidebar";
import { UnderstandHeader } from "@/components/understand/UnderstandHeader";
import { DirectAnswer } from "@/components/guidance/DirectAnswer";
import { FactLawMapping } from "@/components/guidance/FactLawMapping";
import { GuidanceRail } from "@/components/guidance/GuidanceRail";
import { LegalSources } from "@/components/guidance/LegalSources";
import { NextSteps } from "@/components/guidance/NextSteps";
import { SituationSnapshot } from "@/components/guidance/SituationSnapshot";
import { Button } from "@/components/ui/Button";
import { mockLegalRetrieval } from "@/lib/mock-legal-retrieval";
import { useMatter } from "@/providers/MatterProvider";

export function GuidanceWorkspace() {
  const router = useRouter();
  const { matter, setMatter } = useMatter();

  const guidance = matter?.guidance;
  const verified = matter?.stage === "USER_VERIFIED" || matter?.stage === "GUIDANCE_GENERATED";

  useEffect(() => {
    if (!matter || !verified || guidance) {
      return;
    }

    const timer = window.setTimeout(() => {
      const result = mockLegalRetrieval(matter);
      setMatter({
        ...matter,
        guidance: result,
        stage: "GUIDANCE_GENERATED",
      });
    }, 650);

    return () => window.clearTimeout(timer);
  }, [guidance, matter, setMatter, verified]);

  const verifiedFacts = useMemo(
    () => matter?.facts.filter((fact) => fact.state !== "unknown") ?? [],
    [matter],
  );

  if (!matter) {
    return (
      <RouteGuardMessage
        title="Your situation must be verified before legal guidance can be generated."
        text="Start from the intake page so NyayaSaarthi can build and verify the matter context."
        action="Start a Situation"
        onAction={() => router.push("/")}
      />
    );
  }

  if (!verified) {
    return (
      <RouteGuardMessage
        title="Your situation must be verified before legal guidance can be generated."
        text="Review the structured context first. Legal guidance begins only after user verification."
        action="Review Situation"
        onAction={() => router.push("/verify")}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#F7F3EA] text-[#18150F] lg:grid lg:grid-cols-[248px_1fr]">
      <AppSidebar currentStep="guidance" />
      <div className="min-w-0">
        <UnderstandHeader language={matter.language} currentStep="guidance" />
        <main className="px-4 py-5 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-[1440px]">
            <div className="mb-5 rounded-lg border border-[#DED7CA] bg-[#FBF8F1] px-5 py-5 sm:px-6">
              <span className="inline-flex rounded-md border border-[#C49A55]/60 bg-[#F4E8D3] px-3 py-1 text-xs font-extrabold uppercase text-[#7A521F]">
                Verified Context
              </span>
              <span className="ml-2 inline-flex rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 py-1 text-xs font-extrabold uppercase text-[#6B665D]">
                Official Sources Checked
              </span>
              <h1 className="font-editorial mt-3 text-4xl font-bold leading-tight text-[#18150F] sm:text-5xl">
                Guidance for Your Situation
              </h1>
              <p className="mt-3 max-w-4xl text-sm font-semibold leading-6 text-[#6B665D] sm:text-base">
                Based on the situation you verified, NyayaSaarthi has matched relevant Motor
                Vehicle Law sources and explained what they may mean for you.
              </p>
            </div>

            {!guidance ? (
              <RetrievalLoading />
            ) : (
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
                <div className="space-y-5">
                  <DirectAnswer guidance={guidance} />
                  <SituationSnapshot matter={matter} facts={verifiedFacts} />
                  <FactLawMapping guidance={guidance} />
                  <LegalSources sources={guidance.sources} />
                  <NextSteps steps={guidance.nextSteps} />
                  <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
                    <p className="text-xs font-extrabold uppercase text-[#A8752B]">
                      Summary Prepared
                    </p>
                    <h2 className="font-editorial mt-2 text-3xl font-bold text-[#18150F]">
                      Continue to Summary
                    </h2>
                    <p className="mt-2 text-sm font-semibold leading-6 text-[#6B665D]">
                      Page 5 will use this same matter, verified facts, sources, uncertainties and
                      next steps to create the final guidance summary.
                    </p>
                    <button
                      type="button"
                      disabled
                      className="mt-4 inline-flex min-h-11 cursor-not-allowed items-center rounded-md border border-[#DED7CA] bg-[#EFE8DA] px-4 text-sm font-extrabold text-[#6B665D]"
                    >
                      Continue to Summary
                    </button>
                  </section>
                </div>
                <GuidanceRail matter={matter} guidance={guidance} factCount={verifiedFacts.length} />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function RetrievalLoading() {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">
        Checking verified legal sources...
      </p>
      <h2 className="font-editorial mt-3 text-4xl font-bold text-[#18150F]">
        Preparing grounded guidance
      </h2>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {["Matching your verified situation", "Checking relevant official sources", "Preparing grounded guidance"].map(
          (step) => (
            <div key={step} className="rounded-md border border-[#DED7CA] bg-[#FFFDF8] p-4">
              <p className="text-sm font-extrabold text-[#18150F]">{step}</p>
            </div>
          ),
        )}
      </div>
    </section>
  );
}

function RouteGuardMessage({
  title,
  text,
  action,
  onAction,
}: {
  title: string;
  text: string;
  action: string;
  onAction: () => void;
}) {
  return (
    <main className="grid min-h-screen place-items-center bg-[#F7F3EA] px-5 text-[#18150F]">
      <section className="max-w-xl rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-6">
        <p className="text-sm font-extrabold uppercase text-[#A8752B]">Guidance gate</p>
        <h1 className="font-editorial mt-3 text-4xl font-bold text-[#071B3A]">{title}</h1>
        <p className="mt-3 text-sm font-semibold leading-6 text-[#6B665D]">{text}</p>
        <Button className="mt-5" onClick={onAction}>
          {action}
        </Button>
      </section>
    </main>
  );
}
