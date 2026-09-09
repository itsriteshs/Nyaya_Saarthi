import Link from "next/link";
import { ClipboardCheck, FileCheck2, FileText, Home, Scale, Settings, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { key: "understand", label: "Situation / Understand", href: "/understand", icon: ClipboardCheck },
  { key: "verify", label: "Verify", href: "/verify", icon: FileCheck2 },
  { key: "guidance", label: "Guidance", href: "/guidance", icon: Scale },
  { key: "summary", label: "Summary", href: "/summary", icon: FileText },
  { key: "matters", label: "My Matters", href: "#", icon: Home },
];

interface AppSidebarProps {
  currentStep?: "understand" | "verify" | "guidance" | "summary";
}

export function AppSidebar({ currentStep = "understand" }: AppSidebarProps) {
  const order = ["understand", "verify", "guidance", "summary"];
  const currentIndex = order.indexOf(currentStep);

  return (
    <aside className="hidden min-h-screen border-r border-[#132D55] bg-[#071B3A] text-[#F7F3EA] lg:flex lg:flex-col">
      <div className="border-b border-white/10 px-5 py-6">
        <Link href="/" className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-md border border-[#C49A55] text-[#C49A55]">
            <Scale size={20} aria-hidden="true" />
          </span>
          <span>
            <span className="font-editorial block text-2xl font-bold leading-none">
              Nyaya<span className="text-[#C49A55]">Saarthi</span>
            </span>
            <span className="mt-1 block text-xs font-bold text-[#D8CCBA]">
              Motor Vehicle Law Assistant
            </span>
          </span>
        </Link>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-5" aria-label="Application navigation">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.key === currentStep;
          const itemIndex = order.indexOf(item.key);
          const completed = itemIndex >= 0 && itemIndex < currentIndex;

          return (
            <Link
              key={item.label}
              href={item.href}
              className={cn(
                "flex min-h-11 items-center gap-3 rounded-md px-3 text-sm font-extrabold transition-colors",
                active
                  ? "border border-[#C49A55]/55 bg-[#F7F3EA] text-[#071B3A]"
                  : completed
                    ? "border border-white/10 bg-white/8 text-white"
                    : "text-[#E8DDCC] hover:bg-white/8 hover:text-white",
              )}
            >
              <Icon size={17} aria-hidden="true" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-3">
        <button className="flex min-h-11 w-full items-center gap-3 rounded-md px-3 text-sm font-extrabold text-[#E8DDCC] transition-colors hover:bg-white/8 hover:text-white">
          <Settings size={17} aria-hidden="true" />
          Settings
        </button>
        <div className="mt-4 rounded-md border border-white/10 p-3 text-xs font-semibold leading-5 text-[#D8CCBA]">
          <ShieldCheck size={16} className="mb-2 text-[#C49A55]" aria-hidden="true" />
          Context is reviewed before law retrieval.
        </div>
      </div>
    </aside>
  );
}
