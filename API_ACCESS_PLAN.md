# API Access Plan — Post-Sponsor-Meeting (April 19, 2026)

Dr. Ray confirmed the project must source API access through **free tiers, trials, and researcher programs** at zero cost. This document lists every viable source, a ranked action order, and a ready-to-submit application draft for Anthropic's Researcher Access Program.

---

## 1. Ranked action order (do these this week)

| # | Source | Effort | Time to access | Risk of rejection |
|---|---|---|---|---|
| 1 | **Google AI Studio (Gemini)** | Sign up with Google account | Instant | None — free tier is public |
| 2 | **Groq** | Sign up, no credit card | Instant | None |
| 3 | **OpenRouter** | Sign up, $1 free credits | Instant | None |
| 4 | **Together AI** | Sign up, $25 free credits | Instant | None |
| 5 | **Hugging Face Inference API** | Sign up | Instant | None |
| 6 | **Cohere Trial** | Sign up, trial keys | Instant | None |
| 7 | **OpenAI** | New account = $5 trial credit | Instant (while it lasts) | Expires in 3 months |
| 8 | **Anthropic Researcher Access** | Application + review | 2–4 weeks | Medium — academic context helps |
| 9 | **MSU institutional access** | Ask IT / advisor | 1–2 weeks | Low — worth asking |

### Recommended this week
Sign up for **1, 2, 3, 4, 5, 6 today** (all instant, no applications). Submit **#8 Anthropic application** in parallel. Ask Prof. Jain and Dr. Ray's MSU contact about **#9** this week.

---

## 2. Draft — Anthropic Researcher Access Program Application

**Where to apply:** https://www.anthropic.com/research (search "Researcher Access Program") or https://forms.anthropic.com/ (check current URL).

### Field-by-field draft

**Name:** Sheikh Md Faysal (with co-applicant Sonal Kishore, Technical Lead)

**Affiliation:** Feliciano School of Business, Montclair State University — INFO 588 Capstone Program

**Role:** Graduate Student Researcher / Project Lead

**Research project title:**
Enterprise AI Security Red Teaming Platform: Stylistic Variant-Based Vulnerability Assessment for Large Language Models

**Abstract (250 words):**
> We are developing an enterprise-grade platform that systematically evaluates commercial and open-source large language models for security vulnerabilities and regulatory-compliance risks. The platform runs five adversarial attack scenarios — prompt injection, cross-user data leakage, jailbreaks, role manipulation, and policy bypass — and transforms a seed library of 50–100 base prompts into 350–700 stylistic variants using seven transformation techniques (poetry, narrative, metaphor, euphemism, role shift, and others) to detect models that filter only surface-level attacks. Each model response is scored on a CVSS v3.1-weighted 0–10 severity scale and mapped to six compliance frameworks: SOC 2, ISO 27001, GDPR Article 32, CCPA §1798.150, NIST AI RMF, and CPCSC. Output is an auditor-ready report designed for enterprise security and governance teams.
>
> The project is an academic capstone sponsored by Ada Analytics (Dr. Ray Hsu, Industry Sponsor) under the supervision of Prof. Rashmi Jain. Researcher access to the Anthropic API (Claude 3.5 Haiku, Sonnet, Opus) would allow us to include Anthropic models in our comparative evaluation alongside OpenAI, Google, and open-source baselines. All usage will be non-commercial, limited to the capstone timeframe, and published findings will follow Anthropic's responsible-disclosure guidelines. We estimate ~50,000–200,000 tokens total across the research period, primarily low-volume targeted prompts rather than training or fine-tuning workloads.

**Expected token volume:** 50K–200K tokens / month over 4-6 weeks
**Commercial use:** No — academic research only
**Publication plans:** MSU Student Research Symposium 2026; capstone final report
**Sponsor endorsement:** Dr. Ray Hsu, Ada Analytics (available on request)
**Faculty advisor:** Prof. Rashmi Jain (available on request)

### Tips before submitting
- Use your **@montclair.edu email**, not gmail — institutional domains boost approval rates.
- Mention the **sponsor and faculty advisor by name** — adds credibility.
- Offer to **share findings** with Anthropic's safety team — some programs prioritize applicants who contribute back.

---

## 3. Quick-start sign-up links (do these today)

| Provider | URL | What to grab |
|---|---|---|
| Google AI Studio | https://aistudio.google.com/apikey | API key → `GOOGLE_API_KEY` |
| Groq | https://console.groq.com/keys | API key → `GROQ_API_KEY` |
| OpenRouter | https://openrouter.ai/keys | API key → `OPENROUTER_API_KEY` |
| Together AI | https://api.together.xyz/settings/api-keys | API key → `TOGETHER_API_KEY` |
| Hugging Face | https://huggingface.co/settings/tokens | Token → `HF_TOKEN` |
| Cohere | https://dashboard.cohere.com/api-keys | Key → `COHERE_API_KEY` |
| OpenAI | https://platform.openai.com/api-keys | Key → `OPENAI_API_KEY` (uses $5 trial) |

Add each key to `distribution/backend/.env` using the `.env.template` as reference.

---

## 4. Fallback — Ollama (already integrated)

If all above fails, **Ollama runs fully offline, unlimited, free.** Models supported: Llama 3.1, Mistral, Gemma, Phi-3. The platform's `OLLAMA_BASE_URL` is already wired in. This is the guaranteed fallback for the May 4 final presentation.

---

## 5. Ethical note for sponsor conversations

Mentioning free-tier usage is fine. **Do NOT** mention plans to run the full 350–700 variant suite repeatedly against any single provider's free tier — that can trip rate limits and violate ToS. Spread testing across providers: Gemini for one scenario, Groq for another, etc.
