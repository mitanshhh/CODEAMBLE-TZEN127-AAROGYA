"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { TRANSLATION_KEYS, Locale } from "@/lib/translations";
import { API_BASE_URL, apiFetch } from "@/lib/api";

interface LanguageContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
  isTranslating: boolean;
}

const LanguageContext = createContext<LanguageContextType>({
  locale: "en",
  setLocale: () => {},
  t: (key: string) => TRANSLATION_KEYS[key] || key,
  isTranslating: false,
});

export const useLanguage = () => useContext(LanguageContext);

const CACHE_KEY_PREFIX = "aarogya_translations_";

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [isTranslating, setIsTranslating] = useState(false);
  const fetchedRef = useRef<Set<string>>(new Set());

  // Load saved locale from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem("aarogya_locale") as Locale | null;
    if (saved && ["en", "hi", "mr"].includes(saved)) {
      setLocaleState(saved);
    }
  }, []);

  // When locale changes, load cached translations or fetch from API
  useEffect(() => {
    if (locale === "en") {
      setTranslations({});
      return;
    }

    const cacheKey = CACHE_KEY_PREFIX + locale;
    const cached = localStorage.getItem(cacheKey);

    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        setTranslations(parsed);
        return;
      } catch {
        // Cache corrupted, will re-fetch
      }
    }

    // Fetch translations from Google Translate API via our backend
    if (fetchedRef.current.has(locale)) return;
    fetchedRef.current.add(locale);

    const fetchTranslations = async () => {
      setIsTranslating(true);
      try {
        const keys = Object.keys(TRANSLATION_KEYS);
        const texts = Object.values(TRANSLATION_KEYS);

        const res = await apiFetch(`${API_BASE_URL}/api/v1/translate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ texts, target: locale }),
        });

        if (res.ok) {
          const data = await res.json();
          const translationMap: Record<string, string> = {};
          keys.forEach((key, i) => {
            translationMap[key] = data.translations[i];
          });

          setTranslations(translationMap);
          localStorage.setItem(cacheKey, JSON.stringify(translationMap));
        } else {
          console.error("Translation API failed:", await res.text());
          fetchedRef.current.delete(locale);
        }
      } catch (e) {
        console.error("Translation fetch error:", e);
        fetchedRef.current.delete(locale);
      } finally {
        setIsTranslating(false);
      }
    };

    fetchTranslations();
  }, [locale]);

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem("aarogya_locale", newLocale);
  }, []);

  const t = useCallback(
    (key: string): string => {
      if (locale === "en") {
        return TRANSLATION_KEYS[key] || key;
      }
      return translations[key] || TRANSLATION_KEYS[key] || key;
    },
    [locale, translations]
  );

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t, isTranslating }}>
      {children}
    </LanguageContext.Provider>
  );
}
