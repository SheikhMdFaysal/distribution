"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

type ToastVariant = "success" | "error" | "info";

interface Toast {
  id: number;
  message: string;
  variant: ToastVariant;
  duration: number;
}

interface ToastContextValue {
  show: (message: string, variant?: ToastVariant, duration?: number) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

/**
 * Returns a `show` function for triggering toasts from anywhere inside ToastProvider.
 *   const toast = useToast();
 *   toast.show("Test complete", "success");
 */
export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    // Allow safe no-op outside provider so components do not crash in storybook / test contexts
    return { show: () => {} };
  }
  return ctx;
}

/**
 * Wrap the app (or a page) in this provider to enable toasts.
 * Renders a fixed stack in the bottom-right corner.
 */
export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = useCallback(
    (message: string, variant: ToastVariant = "info", duration = 4000) => {
      const id = Date.now() + Math.random();
      setToasts((cur) => [...cur, { id, message, variant, duration }]);
    },
    []
  );

  const dismiss = useCallback((id: number) => {
    setToasts((cur) => cur.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={() => dismiss(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: () => void }) {
  useEffect(() => {
    const id = window.setTimeout(onDismiss, toast.duration);
    return () => window.clearTimeout(id);
  }, [toast.duration, onDismiss]);

  const styles: Record<ToastVariant, string> = {
    success: "border-emerald-500/40 bg-emerald-950/80 text-emerald-200",
    error: "border-rose-500/40 bg-rose-950/80 text-rose-200",
    info: "border-cyan-500/40 bg-cyan-950/80 text-cyan-200",
  };
  const icon: Record<ToastVariant, string> = {
    success: "✓",
    error: "✕",
    info: "ⓘ",
  };

  return (
    <div
      className={`pointer-events-auto flex items-start gap-3 rounded-lg border px-4 py-3 shadow-lg backdrop-blur animate-slide-in-right ${styles[toast.variant]}`}
      role="status"
    >
      <span className="text-lg leading-none mt-0.5">{icon[toast.variant]}</span>
      <p className="text-sm flex-1">{toast.message}</p>
      <button
        type="button"
        onClick={onDismiss}
        className="text-slate-400 hover:text-slate-200 text-sm leading-none"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  );
}
