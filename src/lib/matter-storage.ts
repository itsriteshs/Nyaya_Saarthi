import type { MatterContext } from "@/types/matter";

const STORAGE_KEY = "nyayasaarthi.matter";

// Prototype persistence only.
// The production version will store matter state through the FastAPI backend.
export function loadStoredMatter() {
  if (typeof window === "undefined") {
    return null;
  }

  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as MatterContext;
  } catch {
    window.sessionStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

export function saveStoredMatter(matter: MatterContext | null) {
  if (typeof window === "undefined") {
    return;
  }

  if (!matter) {
    window.sessionStorage.removeItem(STORAGE_KEY);
    return;
  }

  window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(matter));
}
