export function Footer() {
  return (
    <footer className="border-t border-[#DED7CA] bg-[#FBF8F1]">
      <div className="mx-auto grid max-w-7xl gap-5 px-5 py-8 text-sm text-[#6B665D] sm:px-8 lg:grid-cols-[1fr_auto] lg:px-10">
        <div>
          <p className="font-editorial text-2xl font-bold text-[#071B3A]">
            Nyaya<span className="text-[#A8752B]">Saarthi</span>
          </p>
          <p className="mt-1 font-semibold">Motor Vehicle Law guidance prototype</p>
          <p className="mt-3 max-w-3xl">
            NyayaSaarthi provides informational guidance and does not replace professional
            legal advice or official determinations.
          </p>
        </div>
        <nav className="flex flex-wrap items-center gap-4 font-bold text-[#18150F]" aria-label="Footer">
          <a href="#safety" className="hover:text-[#A8752B]">
            Safety
          </a>
          <a href="#sources" className="hover:text-[#A8752B]">
            Official Sources
          </a>
          <a href="#privacy" className="hover:text-[#A8752B]">
            Privacy
          </a>
        </nav>
      </div>
    </footer>
  );
}
