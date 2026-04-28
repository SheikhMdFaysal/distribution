"use client";

import { useEffect, useState } from "react";
import {
  api,
  type AttackScenario,
  type HealthResponse,
  type TestRunDetails,
} from "@/lib/api";

const FREE_MODELS = [
  { adapter: "google", model: "gemini-2.5-flash", vendor: "Google", label: "Gemini 2.5 Flash (Google)" },
  { adapter: "google", model: "gemini-2.0-flash", vendor: "Google", label: "Gemini 2.0 Flash (Google)" },
];

const TECHNIQUES = ["poetry", "narrative", "metaphor", "euphemism", "role_shift"];

export default function DashboardHome() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [scenarios, setScenarios] = useState<AttackScenario[]>([]);
  const [error, setError] = useState<string | null>(null);

  // form state
  const [scenarioId, setScenarioId] = useState<number | null>(null);
  const [techniques, setTechniques] = useState<string[]>(["poetry"]);
  const [modelIdx, setModelIdx] = useState(0);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<TestRunDetails | null>(null);
  const [runError, setRunError] = useState<string | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch((e: Error) => setError(e.message));
    api
      .listScenarios()
      .then((s) => {
        setScenarios(s);
        if (s.length) setScenarioId(s[0].id);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const toggleTechnique = (t: string) => {
    setTechniques((cur) =>
      cur.includes(t) ? cur.filter((x) => x !== t) : [...cur, t]
    );
  };

  const runTest = async () => {
    if (!scenarioId) return;
    const scenario = scenarios.find((s) => s.id === scenarioId);
    if (!scenario) return;

    setRunning(true);
    setRunError(null);
    setResult(null);

    try {
      const model = FREE_MODELS[modelIdx];
      const created = await api.runTest({
        test_name: `Live demo: ${scenario.name} - ${new Date().toISOString()}`,
        description: "Triggered from dashboard",
        attack_scenario_id: scenarioId,
        baseline_prompts: scenario.default_prompts.slice(0, 2), // 2 prompts for speed
        techniques,
        target_models: [
          { adapter: model.adapter, model: model.model, vendor: model.vendor, type: "enterprise" },
        ],
        variants_per_technique: 1,
      });
      const details = await api.getTest(created.test_id);
      setResult(details);
    } catch (e) {
      setRunError(e instanceof Error ? e.message : String(e));
    } finally {
      setRunning(false);
    }
  };

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

        {/* Backend status */}
        <section className="mb-8 rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-lg font-semibold mb-3">Backend Status</h2>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          {health && (
            <div className="grid grid-cols-3 gap-4">
              <Stat label="Status" value={health.status} color="green" />
              <Stat label="Version" value={health.version} color="cyan" />
              <Stat label="Environment" value={health.environment} color="purple" />
            </div>
          )}
        </section>

        {/* Run a test */}
        <section className="mb-8 rounded-xl bg-slate-900 border border-slate-800 p-6">
          <h2 className="text-lg font-semibold mb-4">Run a Security Test</h2>

          {scenarios.length === 0 && <p className="text-slate-400">Loading scenarios...</p>}

          {scenarios.length > 0 && (
            <div className="space-y-5">
              {/* Scenario picker */}
              <div>
                <label className="block text-xs uppercase tracking-wide text-slate-500 mb-2">
                  Attack scenario
                </label>
                <select
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                  value={scenarioId ?? ""}
                  onChange={(e) => setScenarioId(Number(e.target.value))}
                  disabled={running}
                >
                  {scenarios.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
                {scenarioId && (
                  <p className="mt-2 text-xs text-slate-500">
                    {scenarios.find((s) => s.id === scenarioId)?.description}
                  </p>
                )}
              </div>

              {/* Techniques */}
              <div>
                <label className="block text-xs uppercase tracking-wide text-slate-500 mb-2">
                  Stylistic transformation techniques
                </label>
                <div className="flex flex-wrap gap-2">
                  {TECHNIQUES.map((t) => (
                    <button
                      key={t}
                      onClick={() => toggleTechnique(t)}
                      disabled={running}
                      className={`px-3 py-1 rounded text-xs border transition ${
                        techniques.includes(t)
                          ? "bg-cyan-600/20 border-cyan-500 text-cyan-300"
                          : "bg-slate-800 border-slate-700 text-slate-400 hover:border-slate-500"
                      }`}
                    >
                      {t}
                    </button>
                  ))}
                </div>
              </div>

              {/* Model */}
              <div>
                <label className="block text-xs uppercase tracking-wide text-slate-500 mb-2">
                  Target model
                </label>
                <select
                  className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-sm"
                  value={modelIdx}
                  onChange={(e) => setModelIdx(Number(e.target.value))}
                  disabled={running}
                >
                  {FREE_MODELS.map((m, i) => (
                    <option key={i} value={i}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Run button */}
              <button
                onClick={runTest}
                disabled={running || !techniques.length}
                className="w-full py-3 rounded-lg font-semibold transition bg-gradient-to-r from-cyan-500 to-purple-600 hover:from-cyan-400 hover:to-purple-500 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {running ? "Running test... (15-60 seconds)" : "▶  Run security test"}
              </button>
              {runError && (
                <p className="text-red-400 text-sm">Error: {runError}</p>
              )}
            </div>
          )}
        </section>

        {/* Result */}
        {result && <ResultPanel result={result} />}
      </div>
    </main>
  );
}

function Stat({ label, value, color }: { label: string; value: string; color: "green" | "cyan" | "purple" }) {
  const colorMap = { green: "text-green-400", cyan: "text-cyan-400", purple: "text-purple-400" };
  return (
    <div className="rounded-lg bg-slate-800/50 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-bold ${colorMap[color]}`}>{value}</div>
    </div>
  );
}

function ResultPanel({ result }: { result: TestRunDetails }) {
  const riskColor =
    result.risk_level === "HIGH"
      ? "text-red-400"
      : result.risk_level === "MEDIUM"
      ? "text-amber-400"
      : "text-green-400";

  return (
    <section className="rounded-xl bg-slate-900 border border-slate-800 p-6">
      <h2 className="text-lg font-semibold mb-4">Test Result</h2>

      <div className="grid grid-cols-4 gap-3 mb-6">
        <Metric label="Total runs" value={String(result.total_runs)} />
        <Metric
          label="Vulnerabilities"
          value={String(result.vulnerabilities_found)}
          color={result.vulnerabilities_found > 0 ? "text-red-400" : "text-green-400"}
        />
        <Metric
          label="Avg risk score"
          value={result.avg_risk_score?.toFixed(1) ?? "—"}
          color={riskColor}
        />
        <Metric label="Risk level" value={result.risk_level ?? "—"} color={riskColor} />
      </div>

      {/* Per-variant breakdown */}
      <div className="space-y-3">
        {result.baseline_prompts.map((bp) =>
          bp.variants.map((v) => (
            <div key={v.id} className="rounded-lg bg-slate-800/50 p-4 border border-slate-700">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xs uppercase tracking-wide bg-cyan-600/30 text-cyan-300 px-2 py-0.5 rounded">
                  {v.technique}
                </span>
                <span className="text-xs text-slate-500">Original: {bp.prompt_text}</span>
              </div>
              <p className="text-sm text-slate-300 italic mb-2 whitespace-pre-line">
                Variant: {v.variant_text}
              </p>
              {v.model_runs.map((mr) => (
                <div key={mr.id} className="mt-2 pt-2 border-t border-slate-700">
                  <div className="text-xs text-slate-500 mb-1">
                    Model response from {mr.model_name}:
                  </div>
                  <p className="text-sm text-slate-300 mb-2 whitespace-pre-line">
                    {mr.response_text}
                  </p>
                  {mr.evaluation && (
                    <div className="flex gap-3 text-xs">
                      <span
                        className={
                          mr.evaluation.leakage_detected
                            ? "text-red-400"
                            : "text-green-400"
                        }
                      >
                        {mr.evaluation.leakage_detected ? "⚠ Leakage detected" : "✓ No leakage"}
                      </span>
                      <span className="text-slate-400">
                        Risk: {mr.evaluation.risk_score.toFixed(1)} ({mr.evaluation.risk_level})
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          ))
        )}
      </div>
    </section>
  );
}

function Metric({
  label,
  value,
  color = "text-cyan-400",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div className="rounded-lg bg-slate-800/50 p-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-lg font-bold ${color}`}>{value}</div>
    </div>
  );
}
