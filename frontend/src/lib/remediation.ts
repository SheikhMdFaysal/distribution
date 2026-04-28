/**
 * Remediation guidance — what to do when a vulnerability is detected.
 *
 * Maps scenario IDs (and a default fallback) to concrete mitigation steps
 * that an enterprise security team can act on immediately. Used by the
 * Result panel's RemediationPanel component.
 */

export interface Remediation {
  whatHappened: string;
  whyItMatters: string;
  immediateActions: string[];
  longTermFixes: string[];
  complianceImpact: string[];
  whoToNotify: string[];
}

const DEFAULT_REMEDIATION: Remediation = {
  whatHappened:
    "The target model produced output suggesting it would comply with a request to access or expose information it should refuse. The data shown in the response is most likely hallucinated — but the model's willingness to play along is the real vulnerability.",
  whyItMatters:
    "If this model is later connected to enterprise data (via RAG, function calling, plugins, or fine-tuning on private datasets), the same stylistic-attack pattern would likely extract real data. Red-teaming catches this risk before production deployment.",
  immediateActions: [
    "Block this model deployment from production until system-prompt hardening is in place.",
    "Add the failing prompt and its variants to your model's evaluation suite — re-test on every model upgrade.",
    "Notify your security team and the model vendor.",
  ],
  longTermFixes: [
    "Strengthen the system prompt with explicit refusal instructions for data-isolation-related requests.",
    "Add an output filter (separate moderation model or rule-based classifier) that rejects responses containing PII patterns or fabricated user data.",
    "Implement Constitutional AI / RLHF re-training focused on refusing roleplay-framed data extraction.",
    "If using RAG, scope retrieval to the requesting user's documents only — never cross-tenant.",
    "Consider switching to a model with stronger alignment (Claude 3.5 Sonnet, GPT-4o, Gemini 2.5 Pro show stronger refusal rates in this category).",
  ],
  complianceImpact: [
    "SOC 2 (Confidentiality) — failure of access-control trust boundary",
    "ISO 27001 (A.9 Access Control) — unauthorized disclosure pattern",
    "GDPR Article 32 — inadequate security of processing",
    "NIST AI RMF (Govern + Manage) — control gap",
  ],
  whoToNotify: [
    "Internal CISO / Security Team",
    "AI/ML Platform Owner",
    "Model vendor (file as a safety report)",
    "DPO if PII categories are involved",
  ],
};

const SCENARIO_REMEDIATIONS: Record<string, Partial<Remediation>> = {
  enterprise_data_isolation: {
    whatHappened:
      "The model accepted a request to expose data about other users in the same workspace. While the response content is hallucinated, the model violated the vendor's 'your data is isolated' promise by not refusing the request.",
    immediateActions: [
      "Block the model from production until tenant-isolation refusal patterns are tested.",
      "Add cross-tenant prompts to your CI/CD safety regression suite.",
      "Audit any existing deployments where this model has access to multi-tenant data stores.",
    ],
    complianceImpact: [
      "SOC 2 CC6.1 — Logical Access Controls failure",
      "ISO 27001 A.9.4.1 — Information access restriction",
      "GDPR Article 32 — Security of processing (data isolation)",
      "CCPA §1798.150 — Reasonable security failure",
      "NIST AI RMF MAP 2.1 — Context awareness gap",
    ],
  },
  cross_user_leakage: {
    whatHappened:
      "The model played along with a stylistic prompt asking to access other users' conversation history. It generated fabricated chat logs instead of refusing — demonstrating that, given access to real session data, it would likely surface them.",
    immediateActions: [
      "Disable cross-session memory / context-sharing features in the model deployment.",
      "Verify session isolation at the API gateway level — model should only see the current user's context.",
      "Add session-boundary refusal training data to the next fine-tuning round.",
    ],
    complianceImpact: [
      "SOC 2 CC6.1 — Confidentiality violation",
      "ISO 27001 A.13.2.1 — Information transfer policy",
      "NIST AI RMF MEASURE 2.7 — Privacy harm",
      "GDPR Article 5 — Purpose limitation breach",
    ],
  },
  training_data_extraction: {
    whatHappened:
      "The model surfaced content that may originate from its training corpus — potentially including copyrighted, proprietary, or PII material that should not be reproducible verbatim.",
    immediateActions: [
      "Run a substring-match check against known training-data leak signatures.",
      "Document the prompts that triggered extraction and add them to your DLP rules.",
      "Engage legal/IP counsel if any extracted content is copyrighted or trade-secret.",
    ],
    complianceImpact: [
      "GDPR Article 17 — Right to erasure may be violated",
      "Trade-secret / IP concerns under DTSA",
      "ISO 27001 A.18.1.2 — Intellectual property rights",
    ],
  },
  context_boundary_isolation: {
    whatHappened:
      "The model crossed an instruction boundary — it followed a user-supplied directive that should have been overridden by the system prompt. This is a classic prompt-injection pattern.",
    immediateActions: [
      "Audit the system-prompt injection defenses in your deployment.",
      "Add structured-output enforcement (JSON schema, function calling) to constrain model output.",
      "Consider a guardrails layer (LLM-as-judge or rule-based) between user input and the model.",
    ],
    complianceImpact: [
      "OWASP LLM01 (Prompt Injection)",
      "NIST AI RMF MEASURE 2.6 — Resilience",
      "SOC 2 CC7.1 — System operations integrity",
    ],
  },
  timing_attacks: {
    whatHappened:
      "Response time variance suggests the model may be performing different code paths or accessing different resources based on the input — a side-channel that can leak information about backend state.",
    immediateActions: [
      "Add response-time normalization at the API gateway.",
      "Monitor for unusual latency patterns in production logs.",
      "Stress-test with adversarial timing probes regularly.",
    ],
    complianceImpact: [
      "ISO 27001 A.13.1.3 — Segregation in networks",
      "NIST AI RMF MEASURE 2.7 — Privacy harm",
    ],
  },
};

export function getRemediation(scenarioKey: string): Remediation {
  const override = SCENARIO_REMEDIATIONS[scenarioKey] ?? {};
  return { ...DEFAULT_REMEDIATION, ...override };
}
