import { FileText, MessageSquareText, ShieldCheck } from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";

const steps = [
  {
    number: "01",
    title: "Explain Naturally",
    text: "Describe your road or vehicle situation in your own words.",
    icon: MessageSquareText,
  },
  {
    number: "02",
    title: "Complete the Context",
    text: "NyayaSaarthi identifies important details and asks only what is missing.",
    icon: FileText,
  },
  {
    number: "03",
    title: "Receive Grounded Guidance",
    text: "After you verify the situation, relevant official law is retrieved and explained clearly.",
    icon: ShieldCheck,
  },
];

const signatureFlow = ["Understand", "Clarify", "Verify", "Check Law", "Guide"];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="px-5 py-14 sm:px-8 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <div className="border-y border-[#DED7CA] py-6">
          <div className="grid gap-3 md:grid-cols-5 md:items-center">
            {signatureFlow.map((item, index) => (
              <div key={item} className="flex items-center gap-3 md:block">
                <span className="font-editorial text-3xl font-bold text-[#A8752B]">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="mt-0 md:mt-2">
                  <p className="text-sm font-extrabold uppercase text-[#18150F]">{item}</p>
                  {index < signatureFlow.length - 1 ? (
                    <div className="mt-3 hidden h-px bg-[#DED7CA] md:block" aria-hidden="true" />
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="mt-12 max-w-2xl">
          <SectionLabel items={["How it works"]} />
          <h2 className="font-editorial mt-4 text-4xl font-bold leading-tight text-[#18150F] sm:text-5xl">
            Context before answers
          </h2>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {steps.map((step) => {
            const Icon = step.icon;

            return (
              <article
                key={step.title}
                className="rounded-lg border border-[#DED7CA] bg-[#FBF8F1] p-5"
              >
                <div className="flex items-start justify-between gap-4">
                  <span className="font-editorial text-4xl font-bold text-[#A8752B]">
                    {step.number}
                  </span>
                  <span className="grid size-10 place-items-center rounded-md border border-[#DED7CA] text-[#071B3A]">
                    <Icon size={19} aria-hidden="true" />
                  </span>
                </div>
                <h3 className="mt-5 text-lg font-extrabold text-[#18150F]">{step.title}</h3>
                <p className="mt-3 text-sm font-semibold leading-6 text-[#6B665D]">{step.text}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
