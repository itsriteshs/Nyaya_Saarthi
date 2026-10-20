import type { MatterContext } from "@/types/matter";

const STORAGE_KEY = "nyayasaarthi.matter";

// Tab-local pointer/cache for the matter persisted by the FastAPI backend.
export function loadStoredMatter() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const stored: unknown = JSON.parse(raw);
    if (!stored || typeof stored !== "object" || !("id" in stored) || typeof stored.id !== "string" ||
        !("facts" in stored) || !Array.isArray(stored.facts)) return null;
    const matter = stored as MatterContext;
    if (process.env.NEXT_PUBLIC_NYAYA_DEMO_MODE !== "true" && (!matter.nlpAnalysis || !matter.revision)) return null;
    return matter;
  } catch {
    return null;
  }
}

export function saveStoredMatter(matter: MatterContext | null) {
  if (typeof window === "undefined") {
    return;
  }

  try {
    if (!matter) window.sessionStorage.removeItem(STORAGE_KEY);
    else window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(matter));
  } catch {
    // Browser cache is optional; the backend remains the persisted authority.
  }
}
