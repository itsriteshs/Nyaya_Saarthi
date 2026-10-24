import type { Metadata } from "next";
import Link from "next/link";
import Image from "next/image";
import { ArrowRight, BookOpen, CodeXml, GraduationCap, Mail, Scale } from "lucide-react";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";

export const metadata: Metadata = {
  title: "About Us | NyayaSaarthi",
  description: "Meet the NyayaSaarthi student team and faculty guide at Amrita Vishwa Vidyapeetham.",
};

const team = [
  { name: "Jeevan Grandhi", photo: "/team/jeevan-grandhi.jpeg", roll: "CB.SC.U4CSE24015", email: "cb.sc.u4cse24015@cb.students.amrita.edu", github: "https://github.com/munnagrandhi", handle: "munnagrandhi" },
  { name: "Jishnu Nambiar", photo: "/team/jishnu-nambiar.jpeg", roll: "CB.SC.U4CSE24019", email: "cb.sc.u4cse24019@cb.students.amrita.edu", github: "https://github.com/jishnu-nambiar", handle: "jishnu-nambiar" },
  { name: "Ritesh S", photo: "/team/ritesh-s.jpeg", roll: "CB.SC.U4CSE24042", email: "cb.sc.u4cse24042@cb.students.amrita.edu", github: "https://github.com/itsriteshs", handle: "itsriteshs" },
];

export default function AboutPage() {
  return (
    <>
      <Header />
      <main id="main-content" className="mx-auto max-w-7xl px-5 py-12 sm:px-8 sm:py-16 lg:px-10">
        <section aria-labelledby="about-title" className="grid items-center gap-10 lg:grid-cols-[1.35fr_1fr] lg:gap-16">
          <div>
            <p className="text-xs font-extrabold tracking-[0.18em] text-[#8B6023]">ABOUT NYAYASAARTHI</p>
            <h1 id="about-title" className="font-editorial mt-4 text-5xl font-bold leading-[1.05] text-[#071B3A] sm:text-6xl">
              A clearer road to<br className="hidden sm:block" /> understanding your rights.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-[#4F4A42]">
              NyayaSaarthi is a student-built research prototype that helps people explore India’s motor vehicle laws in English, Hindi, and Hinglish.
            </p>
            <p className="mt-3 max-w-2xl text-sm leading-7 text-[#6B665D]">
              From describing a situation to reviewing facts and exploring source-linked guidance, our aim is to make legal information easier to understand.
            </p>
            <a href="https://github.com/itsriteshs/Nyaya_Saarthi" target="_blank" rel="noopener noreferrer" className="mt-6 inline-flex min-h-11 items-center gap-2 text-sm font-extrabold text-[#071B3A] underline decoration-[#C49A55] underline-offset-4">
              <CodeXml size={18} aria-hidden="true" /> Explore the project <ArrowRight size={16} aria-hidden="true" />
            </a>
          </div>
          <aside aria-label="Academic project" className="rounded-xl border border-[#C49A55]/50 bg-[#071B3A] p-7 text-[#F7F3EA] sm:p-9">
            <Scale size={32} className="text-[#D7B477]" aria-hidden="true" />
            <p className="mt-6 text-xs font-bold tracking-[0.16em] text-[#D7B477]">RESEARCH · PRODUCT · SOFTWARE</p>
            <h2 className="font-editorial mt-3 text-3xl font-semibold">Built with curiosity.<br />Guided by evidence.</h2>
            <dl className="mt-7 space-y-4 border-t border-white/15 pt-6 text-sm">
              <div><dt className="text-[#CFC7B9]">Institution</dt><dd className="mt-1 font-bold">Amrita Vishwa Vidyapeetham</dd></div>
              <div><dt className="text-[#CFC7B9]">Course</dt><dd className="mt-1 font-bold">23CSE471 · Natural Language Processing</dd></div>
              <div><dt className="text-[#CFC7B9]">Project group</dt><dd className="mt-1 font-bold">18</dd></div>
            </dl>
          </aside>
        </section>

        <section aria-labelledby="guide-title" className="mt-12 flex flex-col gap-5 rounded-xl border border-[#DED7CA] bg-[#FFFCF5] p-6 sm:flex-row sm:items-center sm:p-8">
          <span className="grid size-14 shrink-0 place-items-center rounded-full border border-[#DED7CA] bg-[#F1E9DA] text-[#8B6023]"><GraduationCap size={27} aria-hidden="true" /></span>
          <div>
            <h2 id="guide-title" className="text-xs font-extrabold tracking-[0.15em] text-[#8B6023]">FACULTY GUIDE</h2>
            <p className="font-editorial mt-2 text-3xl font-bold text-[#071B3A]">Dr. T. Senthil Kumar</p>
            <p className="mt-1 text-sm font-semibold text-[#6B665D]">Professor, CSE Department</p>
          </div>
          <p className="max-w-sm text-sm leading-7 text-[#6B665D] sm:ml-auto">Developed as an academic research project under the guidance of Dr. T. Senthil Kumar.</p>
        </section>

        <section aria-labelledby="team-title" className="mt-14">
          <div className="mb-7 flex flex-wrap items-end justify-between gap-3">
            <div><p className="text-xs font-extrabold tracking-[0.15em] text-[#8B6023]">THE PEOPLE BEHIND THE PROJECT</p><h2 id="team-title" className="font-editorial mt-2 text-4xl font-bold text-[#071B3A]">Meet our team</h2></div>
            <p className="text-sm font-semibold text-[#6B665D]">Group 18 · Amrita Vishwa Vidyapeetham</p>
          </div>
          <div className="grid gap-5 md:grid-cols-3">
            {team.map((member) => (
              <article key={member.roll} className="min-w-0 rounded-xl border border-[#DED7CA] bg-[#FFFCF5] p-6 sm:p-7">
                <Image src={member.photo} alt={`Portrait of ${member.name}`} width={96} height={112} sizes="96px" className="h-28 w-24 rounded-lg border border-[#C49A55]/60 bg-[#F1E9DA] object-cover object-top" />
                <h3 className="font-editorial mt-5 text-3xl font-bold text-[#071B3A]">{member.name}</h3>
                <p className="mt-2 text-xs font-bold tracking-wide text-[#6B665D]">{member.roll}</p>
                <div className="mt-6 grid gap-3 border-t border-[#DED7CA] pt-5 text-sm">
                  <a href={`mailto:${member.email}`} aria-label={`Email ${member.name}`} className="flex min-h-11 items-start gap-2 py-2 font-semibold text-[#4F4A42] hover:text-[#8B6023]"><Mail size={17} className="mt-0.5 shrink-0" aria-hidden="true" /><span className="min-w-0 break-all">{member.email}</span></a>
                  <a href={member.github} target="_blank" rel="noopener noreferrer" aria-label={`${member.name} on GitHub`} className="flex min-h-11 items-center gap-2 font-bold text-[#071B3A] hover:text-[#8B6023]"><CodeXml size={17} className="shrink-0" aria-hidden="true" /><span>{member.handle}</span><ArrowRight size={15} className="ml-auto shrink-0" aria-hidden="true" /></a>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section aria-labelledby="purpose-title" className="mt-12 flex flex-col gap-5 border-t border-[#DED7CA] pt-8 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex max-w-2xl items-start gap-3">
            <BookOpen size={21} className="mt-1 shrink-0 text-[#8B6023]" aria-hidden="true" />
            <div><h2 id="purpose-title" className="text-sm font-extrabold text-[#071B3A]">Learning, research, and responsible guidance</h2><p className="mt-2 text-sm leading-7 text-[#6B665D]">The project supports understanding and research. Users review their facts before guidance, and the information does not replace advice from a qualified legal professional.</p></div>
          </div>
          <Link href="/#home" className="inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-md bg-[#071B3A] px-5 py-3 text-sm font-extrabold !text-white hover:bg-[#102A52]">Try NyayaSaarthi <ArrowRight size={16} aria-hidden="true" /></Link>
        </section>
      </main>
      <Footer />
    </>
  );
}
