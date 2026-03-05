# Platform Architecture

## System Overview

```
┌─────────────┐
│   Browser   │
│  (Frontend) │
└──────┬──────┘
       │ HTTP/REST
       ↓
┌─────────────────────┐
│  FastAPI Backend    │
│  (Port 8080)        │
├─────────────────────┤
│ • Security Testing  │
│ • Variant Generator │
│ • Risk Scorer       │
│ • Compliance Mapper │
└──────┬──────┬───────┘
       │      │
       ↓      ↓
  ┌────────┐ ┌──────────────┐
  │Database│ │ Model APIs   │
  │(SQLite)│ │ • OpenAI     │
  └────────┘ │ • Anthropic  │
             │ • Google     │
             └──────────────┘
```

## Technology Stack

**Backend:**
- FastAPI (Python web framework)
- SQLAlchemy (Database ORM)
- Pydantic (Data validation)
- Redis + RQ (Job queue)

**Frontend:**
- HTML5 + CSS3 + JavaScript
- Responsive design
- Real-time updates

**Model Integrations:**
- OpenAI API (ChatGPT)
- Anthropic API (Claude)
- Google Generative AI (Gemini)
- Ollama (Local models)

**Data Storage:**
- SQLite (Demo/Development)
- PostgreSQL (Production-ready)
- Redis (Job queue)

## Key Components

### 1. Attack Scenario Engine
- 5 pre-configured scenarios
- Extensible framework
- Compliance mapping

### 2. Variant Generator
- Poetry transformation
- Narrative framing
- Metaphorical abstraction
- Role-shift techniques

### 3. Risk Scorer
- 0-10 scale (CVE/CVSS-style)
- Data sensitivity weighting
- Leakage severity assessment
- Confidence scoring

### 4. Compliance Mapper
- SOC2 controls (CC6.1, CC6.6, CC6.7)
- ISO27001 (A.9.2.1, A.9.4.1)
- CPCSC requirements
- GDPR Article 32
- CCPA Section 1798.150
- NIST AI RMF

## Security Considerations

- API keys stored in .env (never committed)
- Input validation on all endpoints
- Rate limiting for external APIs
- Audit logging for compliance
