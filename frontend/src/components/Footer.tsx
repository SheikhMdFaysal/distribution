"use client";

import { useState } from "react";
import { AboutModal } from "./AboutModal";

const APP_VERSION = "1.2.0";
const CURRENT_YEAR = new Date().getFullYear();

/**
 * Footer with version, copyright, and lightweight legal links.
 * Rendered at the bottom of every page via the root layout.
 */
export function Footer() {
  const [aboutOpen, setAboutOpen] = useState(false);

  return (
    <>
      <footer className="mt-16 border-t border-slate-800 bg-slate-950 text-slate-500">
        <div className="mx-auto max-w-6xl px-8 py-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-3">
            <span>© {CURRENT_YEAR} Ada Analytics. All rights reserved.</span>
          </div>
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setAboutOpen(true)}
              className="hover:text-slate-300 transition"
              aria-label="About this platform"
            >
              About
            </button>
            <a
              href="/privacy"
              className="hover:text-slate-300 transition"
              aria-label="Privacy policy"
            >
              Privacy
            </a>
            <a
              href="/terms"
              className="hover:text-slate-300 transition"
              aria-label="Terms of service"
            >
              Terms
            </a>
            <a
              href="https://github.com/SheikhMdFaysal/distribution"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-300 transition"
              aria-label="GitHub repository"
            >
              GitHub
            </a>
            <span className="text-slate-600">v{APP_VERSION}</span>
          </div>
        </div>
      </footer>

      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </>
  );
}
