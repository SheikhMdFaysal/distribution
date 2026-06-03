"use client";

import { useEffect } from "react";

interface AboutModalProps {
  open: boolean;
  onClose: () => void;
}

const APP_VERSION = "1.1.2";

/**
 * Modal showing platform credits, sponsor info, and origin.
 * Opened from the footer's "About" link.
 */
export function AboutModal({ open, onClose }: AboutModalProps) {
  // Close on Escape and lock body scroll while open
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = prevOverflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="about-title"
    >
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal panel */}
      <div className="relative w-full max-w-lg rounded-2xl border border-slate-700 bg-slate-900 p-7 shadow-2xl">
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-500 hover:text-slate-200 text-xl leading-none"
          aria-label="Close"
        >
          ×
        </button>

        <div className="mb-5">
          <h2
            id="about-title"
            className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent"
          >
            About this platform
          </h2>
          <p className="mt-1 text-xs text-slate-500">
            Enterprise AI Security Red Teaming Platform · v{APP_VERSION}
          </p>
        </div>

        <div className="space-y-5 text-sm">
          <CreditRow label="Developer Team Lead" name="Sheikh Md Faysal">
            <SocialLink
              href="https://www.linkedin.com/in/faysal-msba"
              label="LinkedIn"
            />
            <SocialLink
              href="https://sheikhmdfaysal.github.io/SheikhMdFaysal/"
              label="Portfolio"
            />
          </CreditRow>

          <CreditRow label="Industry Sponsor" name="Dr. Ray Hsu" />

          <div className="pt-2 border-t border-slate-800">
            <p className="text-xs text-slate-500 leading-relaxed">
              Originally built as the INFO 588 Capstone project at the{" "}
              <span className="text-slate-300">
                Feliciano School of Business, Montclair State University
              </span>
              . Now commercialized through Ada Analytics.
            </p>
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-500">© 2026 Ada Analytics</span>
            <a
              href="https://github.com/SheikhMdFaysal/distribution"
              target="_blank"
              rel="noopener noreferrer"
              className="text-cyan-400 hover:text-cyan-300"
            >
              View source →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

function CreditRow({
  label,
  name,
  children,
}: {
  label: string;
  name: string;
  children?: React.ReactNode;
}) {
  return (
    <div>
      <div className="text-[10px] uppercase tracking-wider text-slate-500 mb-0.5">
        {label}
      </div>
      <div className="text-slate-100 font-medium">{name}</div>
      {children && (
        <div className="mt-1.5 flex items-center gap-3">{children}</div>
      )}
    </div>
  );
}

function SocialLink({ href, label }: { href: string; label: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-xs text-cyan-400 hover:text-cyan-300"
    >
      {label} →
    </a>
  );
}
