"use client";

import { Menu, Scale, X } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Home", href: "#home" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Safety", href: "#safety" },
  { label: "Official Sources", href: "#sources" },
];

export function Header() {
  const [open, setOpen] = useState(false);

  function focusIntake() {
    document.getElementById("home")?.scrollIntoView({ behavior: "smooth", block: "start" });
    window.setTimeout(() => document.getElementById("situation")?.focus(), 250);
    setOpen(false);
  }

  return (
    <header className="sticky top-0 z-40 border-b border-[#DED7CA] bg-[#FBF8F1]/95 backdrop-blur">
      <div className="mx-auto flex h-20 max-w-7xl items-center justify-between gap-4 px-5 sm:px-8 lg:px-10">
        <a href="#home" className="flex min-w-0 items-center gap-3" aria-label="NyayaSaarthi home">
          <span className="grid size-11 shrink-0 place-items-center rounded-md border border-[#C49A55] bg-[#071B3A] text-[#F7F3EA]">
            <Scale size={22} strokeWidth={1.8} aria-hidden="true" />
          </span>
          <span className="min-w-0">
            <span className="font-editorial block text-2xl font-bold leading-none text-[#071B3A] sm:text-3xl">
              Nyaya<span className="text-[#A8752B]">Saarthi</span>
            </span>
            <span className="block truncate text-xs font-bold text-[#6B665D]">
              Your Road. Your Rights. Your Legal Guide.
            </span>
          </span>
        </a>

        <nav className="hidden items-center gap-7 lg:flex" aria-label="Primary navigation">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="text-sm font-extrabold text-[#18150F] transition-colors hover:text-[#A8752B]"
            >
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 lg:flex">
          <label className="sr-only" htmlFor="site-language">
            Language
          </label>
          <select
            id="site-language"
            className="h-11 rounded-md border border-[#DED7CA] bg-[#FBF8F1] px-3 text-sm font-bold text-[#18150F]"
            defaultValue="english"
          >
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="hinglish">Hinglish</option>
          </select>
          <Button className="px-5" onClick={focusIntake}>
            Ask NyayaSaarthi
          </Button>
        </div>

        <button
          type="button"
          className="grid size-11 place-items-center rounded-md border border-[#DED7CA] bg-[#FBF8F1] text-[#071B3A] lg:hidden"
          aria-label={open ? "Close menu" : "Open menu"}
          aria-expanded={open}
          onClick={() => setOpen((value) => !value)}
        >
          {open ? <X size={21} aria-hidden="true" /> : <Menu size={21} aria-hidden="true" />}
        </button>
      </div>

      <div
        className={cn(
          "border-t border-[#DED7CA] bg-[#FBF8F1] px-5 py-4 lg:hidden",
          open ? "block" : "hidden",
        )}
      >
        <nav className="grid gap-2" aria-label="Mobile navigation">
          {navItems.map((item) => (
            <a
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-3 text-sm font-extrabold hover:bg-[#EFE8DA]"
              onClick={() => setOpen(false)}
            >
              {item.label}
            </a>
          ))}
        </nav>
        <div className="mt-4 grid gap-3 border-t border-[#DED7CA] pt-4">
          <select
            className="h-11 rounded-md border border-[#DED7CA] bg-[#FBF8F1] px-3 text-sm font-bold"
            defaultValue="english"
            aria-label="Language"
          >
            <option value="english">English</option>
            <option value="hindi">Hindi</option>
            <option value="hinglish">Hinglish</option>
          </select>
          <Button onClick={focusIntake}>Ask NyayaSaarthi</Button>
        </div>
      </div>
    </header>
  );
}
