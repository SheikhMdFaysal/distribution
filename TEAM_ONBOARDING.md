# Team Onboarding — Run the Platform on Your Computer

**For:** Sonal Kishore, Arti Sharma, Baquer Hussain, Sai Akash Kethineni
**Project:** Enterprise AI Security Red Teaming Platform — INFO 588 Capstone
**Maintained by:** Sheikh Md Faysal

This guide gives you three ways to access the platform: **(1) cloud URL** — easiest, just open a browser; **(2) full local setup** — for technical members who want to run everything; **(3) read-only PPTX walkthrough** — slides only.

---

## ⭐ Option 1 — Use the Cloud URL (recommended for everyone)

Once deployed, the platform will be live at:

> **https://ai-security-platform.onrender.com** *(URL will be confirmed after deployment — Faysal will share in WhatsApp group)*

- Open in any browser (Chrome, Edge, Safari).
- **No installation needed.** No accounts. No keys.
- Works on phone, tablet, laptop.

If the page is slow on first load, wait 30 seconds — Render's free tier sleeps inactive servers and takes a moment to wake up.

---

## 🛠 Option 2 — Run It Locally on Your Laptop

Use this if you want to develop, test changes, or demo offline.

### Prerequisites — install once

| Tool | Download | Verify in terminal |
|---|---|---|
| Python 3.11 or newer | https://www.python.org/downloads/ | `python --version` |
| Node.js 20 or newer | https://nodejs.org/ | `node --version` |
| Redis | Windows: https://github.com/tporadowski/redis/releases<br>Mac: `brew install redis`<br>Linux: `sudo apt install redis-server` | `redis-cli ping` → `PONG` |
| Git | https://git-scm.com/ | `git --version` |
| Ollama (optional, for offline LLM testing) | https://ollama.com/download | `ollama --version` |

### Step 1 — Clone the repository

Open **PowerShell** (Windows) or **Terminal** (Mac/Linux), then:

```bash
cd Documents
git clone https://github.com/SheikhMdFaysal/distribution.git ai-security-platform
cd ai-security-platform
```

### Step 2 — Set up the backend

```bash
cd backend
python -m venv venv
```

**On Windows:**
```powershell
venv\Scripts\activate
```

**On Mac/Linux:**
```bash
source venv/bin/activate
```

Then install dependencies:
```bash
pip install -r requirements.txt
```

### Step 3 — Configure API keys

Copy the template:
```bash
copy .env.template .env       # Windows
cp .env.template .env         # Mac/Linux
```

Open `.env` in any text editor (Notepad, VS Code) and paste the API keys Faysal will share with you privately via WhatsApp:

```env
GOOGLE_API_KEY=AIza...
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-...
HF_TOKEN=hf_...
TOGETHER_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=sqlite:///./app.db
REDIS_URL=redis://localhost:6379/0
```

⚠️ **Never share `.env` publicly. Never commit it to GitHub.** It is already in `.gitignore`.

### Step 4 — Initialize the database

```bash
alembic upgrade head
```

### Step 5 — Start Redis (if not already running)

**Windows:** Run Redis from where you installed it (usually `redis-server.exe`).
**Mac:** `brew services start redis`
**Linux:** `sudo systemctl start redis`

Verify with `redis-cli ping` — should return `PONG`.

### Step 6 — Start the backend (in one terminal)

From `ai-security-platform/backend/`, with venv activated:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
```

Should print: `Uvicorn running on http://127.0.0.1:8080`

### Step 7 — Start the RQ worker (in a second terminal)

Open a new terminal, activate venv again, then:
```bash
cd Documents/ai-security-platform/backend
python start_worker.py
```

### Step 8 — Start the frontend (in a third terminal)

```bash
cd Documents/ai-security-platform/frontend
npm install
npm run dev
```

Should print: `Local: http://localhost:3000`

### Step 9 — Open the platform

Visit **http://localhost:3000** in your browser.

You should see the dashboard with the Backend Status card showing **"healthy"** in green.

---

## 🚦 Quick health check — is everything running?

| Service | URL | Expected |
|---|---|---|
| Backend API | http://localhost:8080/api/v1/health | `{"status":"healthy",...}` |
| Frontend | http://localhost:3000 | Dashboard loads |
| Redis | `redis-cli ping` | `PONG` |
| Worker | terminal output | `*** Listening on default...` |

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `python: command not found` | Reinstall Python and tick "Add to PATH" |
| `redis-cli ping` fails | Redis isn't running — start the service |
| Port 8080 already in use | `netstat -ano \| findstr :8080`, then `taskkill /PID <number> /F` |
| Port 3000 already in use | Same as above for `:3000` |
| `npm install` fails | Delete `node_modules/` and `package-lock.json`, retry |
| Database errors after pulling new code | Re-run `alembic upgrade head` |
| Backend shows red error on frontend | Backend isn't running — restart Step 6 |

---

## 📂 Project structure

```
ai-security-platform/
├── README.md                    Project overview
├── ARCHITECTURE.md              Technical design
├── SECURITY_METHODOLOGY_GUIDE.md  Red-teaming methodology
├── DEMO_NOTES.md                Demo walkthrough
├── TEAM_ONBOARDING.md           This file
├── API_ACCESS_PLAN.md           How we obtain API keys
├── DEPLOYMENT_PLAN.md           Cloud deployment strategy
├── FULL_DEMO.html               Old demo UI (kept for reference)
├── RUN.bat / RUN.sh / run.py    Quick-start scripts
│
├── backend/                     FastAPI backend
│   ├── app/                     Source code
│   ├── alembic/                 Database migrations
│   ├── tests/                   Unit tests
│   ├── requirements.txt         Python dependencies
│   ├── Dockerfile               For Render deployment
│   └── .env.template            Env var reference
│
└── frontend/                    Next.js frontend (NEW — production replacement for FULL_DEMO.html)
    ├── src/
    │   ├── app/                 Pages (App Router)
    │   └── lib/api.ts           Typed API client
    ├── .env.local               Frontend env vars
    └── package.json             Node dependencies
```

---

## 🔒 Security rules — read before you commit

1. **Never** commit `.env`, `api_keys.txt`, or any file containing real API keys.
2. **Never** push to `main` without testing locally first.
3. **Never** share API keys in public Slack, GitHub issues, or screenshots.
4. **Always** run the application against your own local Redis and SQLite — do not point it at the cloud production database while testing.
5. If you accidentally commit a secret, **immediately notify Faysal** so the key can be rotated.

---

## 📞 Support

| Question type | Contact |
|---|---|
| "How do I install X?" | Group WhatsApp |
| "Backend code / API logic" | Sonal Kishore |
| "Project status / sponsor / deadlines" | Sheikh Md Faysal |
| "Frontend / dashboard" | Sheikh Md Faysal (then Sonal) |
| "Deployment / Render issues" | Sheikh Md Faysal |

---

## 🗓 Final presentation: **May 4, 2026**

Please make sure you have run through this onboarding at least once **before April 30** so we can rehearse together.

Thank you for being part of this team.

— Sheikh Md Faysal
