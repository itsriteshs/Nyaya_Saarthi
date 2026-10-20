"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { loadStoredMatter, saveStoredMatter } from "@/lib/matter-storage";
import type { MatterContext } from "@/types/matter";
import type { LanguageOption } from "@/types/nlp";

interface MatterProviderValue {
  matter: MatterContext | null;
  restored: boolean;
  intakeLanguage: LanguageOption;
  setIntakeLanguage: (language: LanguageOption) => void;
  setMatter: (matter: MatterContext | null) => void;
  updateMatter: (updater: (matter: MatterContext) => MatterContext) => void;
}

const MatterContextValue = createContext<MatterProviderValue | undefined>(undefined);

export function MatterProvider({ children }: { children: React.ReactNode }) {
  const [matter, setMatterState] = useState<MatterContext | null>(null);
  const [restored, setRestored] = useState(false);
  const [intakeLanguage, setIntakeLanguage] = useState<LanguageOption>("auto");

  // Keep the server and first client render identical, then restore this tab's
  // persisted matter after hydration.
  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      setMatterState(loadStoredMatter());
      setRestored(true);
    });
    return () => window.cancelAnimationFrame(frame);
  }, []);

  const setMatter = useCallback((nextMatter: MatterContext | null) => {
    setMatterState(nextMatter);
    saveStoredMatter(nextMatter);
  }, []);

  const updateMatter = useCallback((updater: (matter: MatterContext) => MatterContext) => {
    setMatterState((current) => {
      if (!current) {
        return current;
      }

      const nextMatter = updater(current);
      saveStoredMatter(nextMatter);
      return nextMatter;
    });
  }, []);

  const value = useMemo(
    () => ({
      matter,
      restored,
      intakeLanguage,
      setIntakeLanguage,
      setMatter,
      updateMatter,
    }),
    [matter, restored, intakeLanguage, setMatter, updateMatter],
  );

  return <MatterContextValue.Provider value={value}>{children}</MatterContextValue.Provider>;
}

export function useMatter() {
  const value = useContext(MatterContextValue);

  if (!value) {
    throw new Error("useMatter must be used inside MatterProvider");
  }

  return value;
}
