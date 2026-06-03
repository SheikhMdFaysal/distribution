"use client";

import { useEffect, useState } from "react";

type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "ai-security-theme";

function applyTheme(theme: Theme) {
  const root = document.documentElement;
  const resolved =
    theme === "system"
      ? window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light"
      : theme;
  root.classList.toggle("dark", resolved === "dark");
  root.dataset.theme = resolved;
}

/**
 * Three-way theme toggle: light, dark, system.
 * Persists choice in localStorage and listens to system theme changes when in system mode.
 */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("system");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = (localStorage.getItem(STORAGE_KEY) as Theme | null) || "system";
    setTheme(saved);
    applyTheme(saved);
    setMounted(true);

    // Listen to system theme changes if user is on "system" mode
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      const current = (localStorage.getItem(STORAGE_KEY) as Theme | null) || "system";
      if (current === "system") applyTheme("system");
    };
    media.addEventListener("change", handler);
    return () => media.removeEventListener("change", handler);
  }, []);

  const choose = (t: Theme) => {
    setTheme(t);
    localStorage.setItem(STORAGE_KEY, t);
    applyTheme(t);
  };

  if (!mounted) {
    // Render a placeholder of identical width to prevent layout shift on hydration
    return <div className="h-7 w-[88px]" aria-hidden />;
  }

  const buttonClass = (t: Theme) =>
    `p-1.5 rounded transition ${
      theme === t
        ? "bg-slate-700 text-cyan-300"
        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
    }`;

  return (
    <div className="flex items-center gap-0.5 rounded-md border border-slate-700 bg-slate-900 p-0.5">
      <button
        type="button"
        onClick={() => choose("light")}
        className={buttonClass("light")}
        aria-label="Light theme"
        title="Light theme"
      >
        <SunIcon />
      </button>
      <button
        type="button"
        onClick={() => choose("system")}
        className={buttonClass("system")}
        aria-label="System theme"
        title="System theme"
      >
        <MonitorIcon />
      </button>
      <button
        type="button"
        onClick={() => choose("dark")}
        className={buttonClass("dark")}
        aria-label="Dark theme"
        title="Dark theme"
      >
        <MoonIcon />
      </button>
    </div>
  );
}

function SunIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function MonitorIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" />
      <path d="M8 21h8M12 17v4" />
    </svg>
  );
}
