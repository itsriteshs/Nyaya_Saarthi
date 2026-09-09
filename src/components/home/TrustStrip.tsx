const principles = [
  {
    title: "Multilingual",
    text: "English, Hindi and Hinglish",
  },
  {
    title: "Context Before Answers",
    text: "Missing details are clarified first",
  },
  {
    title: "Official Sources",
    text: "Guidance is grounded in verified legal material",
  },
  {
    title: "Explainable",
    text: "User facts, official law and system interpretation remain distinguishable",
  },
];

export function TrustStrip() {
  return (
    <section id="safety" className="px-5 py-14 sm:px-8 lg:px-10">
      <div className="mx-auto max-w-7xl rounded-lg bg-[#071B3A] px-5 py-8 text-[#F7F3EA] sm:px-8 lg:px-10">
        <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr] lg:items-start">
          <div>
            <p className="text-sm font-extrabold uppercase text-[#C49A55]">Safety principles</p>
            <h2 className="font-editorial mt-3 text-4xl font-bold leading-tight text-balance">
              Built for careful legal guidance
            </h2>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {principles.map((principle) => (
              <article
                key={principle.title}
                id={principle.title === "Official Sources" ? "sources" : undefined}
                className="border-t border-[#C49A55]/45 pt-4"
              >
                <h3 className="text-base font-extrabold">{principle.title}</h3>
                <p className="mt-2 text-sm font-semibold leading-6 text-[#E8DDCC]">
                  {principle.text}
                </p>
              </article>
            ))}
          </div>
        </div>
        <p id="privacy" className="mt-8 max-w-4xl border-t border-[#C49A55]/45 pt-5 text-sm font-semibold leading-6 text-[#E8DDCC]">
          The prototype separates user-provided facts, retrieved law and system interpretation so
          later guidance can stay auditable.
        </p>
      </div>
    </section>
  );
}
