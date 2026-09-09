import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import type { GuidanceResult } from "@/types/matter";

interface DirectAnswerProps {
  guidance: GuidanceResult;
}

export function DirectAnswer({ guidance }: DirectAnswerProps) {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-xs font-extrabold uppercase text-[#A8752B]">What this means</p>
          <h2 className="font-editorial mt-2 text-3xl font-bold leading-tight text-[#18150F]">
            Based on your verified situation
          </h2>
        </div>
        <Link
          href="/verify"
          className="inline-flex min-h-10 items-center justify-center gap-2 rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-3 text-sm font-extrabold text-[#071B3A] transition-colors hover:border-[#A8752B]"
        >
          <ArrowLeft size={16} aria-hidden="true" />
          Edit Situation
        </Link>
      </div>
      <p className="mt-5 max-w-4xl text-lg font-bold leading-8 text-[#18150F]">
        {guidance.directAnswer}
      </p>
      <p className="mt-3 max-w-4xl border-l-2 border-[#A8752B] pl-4 text-sm font-semibold leading-6 text-[#6B665D]">
        {guidance.qualification}
      </p>
    </section>
  );
}
