import type { NextStep } from "@/types/matter";

interface NextStepsProps {
  steps: NextStep[];
}

export function NextSteps({ steps }: NextStepsProps) {
  return (
    <section className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5 sm:p-6">
      <p className="text-xs font-extrabold uppercase text-[#A8752B]">What You Can Do Now</p>
      <div className="mt-4 divide-y divide-[#DED7CA]">
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
