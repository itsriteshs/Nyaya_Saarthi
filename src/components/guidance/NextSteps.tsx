import type { NextStep } from "@/types/matter";

interface NextStepsProps {
  steps: NextStep[];
}

export function NextSteps({ steps }: NextStepsProps) {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">What You Can Do Now</p>
      <div className="mt-4 divide-y divide-[#DED7CA]">
        {steps.length === 0 ? <p className="text-sm font-semibold leading-6 text-[#6B665D]">
          No source-backed procedure is available for this situation in the reviewed records. If you received an official notice, keep a copy and note its issuing authority, date, and cited provision. Those details can help you check the current official source or get a qualified review; this app cannot verify a fine amount or response deadline here.
        </p> : null}
        {steps.map((step, index) => (
          <article key={step.id} className="grid gap-3 py-4 first:pt-0 sm:grid-cols-[48px_1fr_auto]">
            <span className="font-editorial text-3xl font-bold leading-none text-[#A8752B]">
              {String(index + 1).padStart(2, "0")}
            </span>
            <div>
              <h3 className="text-base font-extrabold text-[#18150F]">{step.title}</h3>
              <p className="mt-1 text-sm font-semibold leading-6 text-[#6B665D]">
                {step.description}
              </p>
            </div>
            <span className="h-fit rounded-md border border-[#DED7CA] bg-[#FFFDF8] px-2 py-1 text-[0.68rem] font-extrabold uppercase text-[#6B665D]">
              {step.tag}
            </span>
          </article>
        ))}
      </div>
    </section>
  );
}
