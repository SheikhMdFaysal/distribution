"use client";

import { useEffect, useState } from "react";
import { api, type HealthResponse } from "@/lib/api";

export default function DashboardHome() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-8">
      <div className="mx-auto max-w-6xl">
        <header className="mb-10">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
            Enterprise AI Security Red Teaming Platform
          </h1>
          <p className="mt-2 text-slate-400">
            Stress-test AI models for security vulnerabilities and compliance risks.
          </p>
        </header>

        {/* Backend status card */}
        <section className="mb-8 rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-lg font-semibold mb-3">Backend Status</h2>
          {error && (
            <p className="text-red-400">
              Could not reach backend at{" "}
              <code className="bg-slate-800 px-2 py-0.5 rounded">
                {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080"}
              </code>
              <br />
              <span className="text-sm text-slate-500">{error}</span>
            </p>
          )}
          {!error && !health && <p className="text-slate-400">Checking…</p>}
          {health && (
            <div className="grid grid-cols-3 gap-4">
              <StatCard label="Status" value={health.status} color="green" />
              <StatCard label="Version" value={health.version} color="cyan" />
              <StatCard label="Environment" value={health.environment} color="purple" />
            </div>
          )}
        </section>

        {/* Feature cards — placeholders for Sonal to build out */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FeatureCard
            title="Attack Scenarios"
            description="5 adversarial vectors: prompt injection, leakage, jailbreaks, role manipulation, policy bypass."
          />
          <FeatureCard
            title="Variant Engine"
            description="350–700 stylistic variants per scenario: poetry, metaphor, narrative, role-shift."
          />
          <FeatureCard
            title="Compliance Mapping"
            description="SOC 2, ISO 27001, GDPR Art. 32, CCPA §1798.150, NIST AI RMF, CPCSC."
          />
        </section>

        <footer className="mt-12 text-center text-sm text-slate-500">
          Next.js scaffold · INFO 588 Capstone · Feliciano School of Business
        </footer>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: "green" | "cyan" | "purple";
}) {
  const colorMap = {
    green: "text-green-400",
    cyan: "text-cyan-400",
    purple: "text-purple-400",
  };
  return (
    <div className="rounded-lg bg-slate-800/50 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-bold ${colorMap[color]}`}>{value}</div>
    </div>
  );
}

function FeatureCard({ title, description }: { title: string; description: string }) {
  return (
    <div className="rounded-xl bg-slate-900 border border-slate-800 p-6 hover:border-cyan-500/50 transition">
      <h3 className="text-lg font-semibold text-cyan-400 mb-2">{title}</h3>
      <p className="text-sm text-slate-400">{description}</p>
    </div>
  );
}
