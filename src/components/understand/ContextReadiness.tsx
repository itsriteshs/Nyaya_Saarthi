interface ContextReadinessProps {
  readiness: {
    found: number;
    total: number;
    percent: number;
  };
}

export function ContextReadiness({ readiness }: ContextReadinessProps) {
  return (
    <section className="mt-5 border-t border-[#DED7CA] pt-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 className="text-xs font-extrabold uppercase text-[#6B665D]">Context readiness</h2>
          <p className="mt-1 text-lg font-extrabold text-[#18150F]">
            {readiness.found} of {readiness.total} important details established
          </p>
        </div>
        <span className="text-sm font-extrabold text-[#A8752B]">{readiness.percent}%</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#E5DDCF]">
        <div
          className="h-full rounded-full bg-[#A8752B] transition-all"
          style={{ width: `${readiness.percent}%` }}
        />
      </div>
    </section>
  );
}
