import sys
# Force UTF-8 stdout/stderr so prints with Unicode (e.g. Gemini responses) don't crash on Windows cp1252.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
import os

from app.core.config import settings
from app.models.database import init_db, get_session_local
from app.api.routes import security_tests, variants, analytics, health

# Initialize database on startup
init_db()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise AI Security Red Teaming Platform API",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
def get_db():
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(security_tests.router, prefix="/api/v1", tags=["security-tests"])
app.include_router(variants.router, prefix="/api/v1", tags=["variants"])
app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enterprise AI Security Platform</title>
    <script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
    <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0f172a; }
        .gradient-bg { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }
        .card { background: rgba(30, 41, 59, 0.8); backdrop-filter: blur(10px); }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; }
        .status-online { background: #22c55e; animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body class="gradient-bg min-h-screen text-white">
    <div id="root"></div>

    <script type="text/babel">
        const { useState, useEffect } = React;
        const API_BASE = '/api/v1';

        function App() {
            const [scenarios, setScenarios] = useState([]);
            const [models, setModels] = useState([]);
            const [loading, setLoading] = useState(true);

            useEffect(() => {
                Promise.all([
                    fetch(API_BASE + '/attack-scenarios').then(r => r.json()),
                    fetch(API_BASE + '/models').then(r => r.json())
                ]).then(([s, m]) => {
                    setScenarios(s);
                    setModels(m.models || []);
                    setLoading(false);
                }).catch(() => setLoading(false));
            }, []);

            if (loading) {
                return (
                    <div className="flex items-center justify-center h-screen">
                        <div className="text-center">
                            <div className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
                            <p className="mt-4 text-slate-400">Loading...</p>
                        </div>
                    </div>
                );
            }

            return (
                <div className="min-h-screen">
                    <nav className="bg-slate-800/80 border-b border-slate-700">
                        <div className="max-w-7xl mx-auto px-4 py-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-lg">
                                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                                    </svg>
                                </div>
                                <div>
                                    <h1 className="text-xl font-bold">Enterprise AI Security</h1>
                                    <p className="text-xs text-slate-400">Red Teaming Platform</p>
                                </div>
                            </div>
                        </div>
                    </nav>

                    <main className="max-w-7xl mx-auto px-4 py-8">
                        <h2 className="text-3xl font-bold mb-8">Security Testing Dashboard</h2>

                        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                            <div className="card p-6 rounded-xl border border-slate-700">
                                <p className="text-slate-400 text-sm">Attack Scenarios</p>
                                <p className="text-3xl font-bold text-cyan-400">{scenarios.length}</p>
                            </div>
                            <div className="card p-6 rounded-xl border border-slate-700">
                                <p className="text-slate-400 text-sm">Available Models</p>
                                <p className="text-3xl font-bold text-purple-400">{models.length}</p>
                            </div>
                            <div className="card p-6 rounded-xl border border-slate-700">
                                <p className="text-slate-400 text-sm">API Status</p>
                                <p className="text-3xl font-bold text-green-400">Online</p>
                            </div>
                            <div className="card p-6 rounded-xl border border-slate-700">
                                <p className="text-slate-400 text-sm">Version</p>
                                <p className="text-3xl font-bold text-slate-400">1.0</p>
                            </div>
                        </div>

                        <div className="card rounded-xl border border-slate-700 p-6 mb-8">
                            <h3 className="text-xl font-bold mb-4">Attack Scenarios</h3>
                            <div className="grid gap-4">
                                {scenarios.map((scenario, i) => (
                                    <div key={i} className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                                        <h4 className="font-semibold">{scenario.name}</h4>
                                        <p className="text-sm text-slate-400 mt-1">{scenario.description}</p>
                                        <p className="text-xs text-cyan-400 mt-2">Tests: "{scenario.vendor_promise_tested}"</p>
                                        <div className="flex flex-wrap gap-2 mt-3">
                                            {scenario.attack_techniques.map((tech, j) => (
                                                <span key={j} className="px-2 py-1 bg-cyan-500/20 text-cyan-400 rounded text-xs capitalize">{tech}</span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="card rounded-xl border border-slate-700 p-6">
                            <h3 className="text-xl font-bold mb-4">Available Models</h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {models.map((model, i) => (
                                    <div key={i} className="bg-slate-700/50 p-4 rounded-lg border border-slate-600">
                                        <div className="flex items-center justify-between">
                                            <span className="font-semibold capitalize">{model.vendor}</span>
                                            <span className={`px-2 py-1 rounded text-xs ${model.type === 'local' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>{model.type}</span>
                                        </div>
                                        <p className="text-sm text-slate-400 mt-2">{model.model}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </main>

                    <footer className="border-t border-slate-700 mt-12 py-6">
                        <div className="max-w-7xl mx-auto px-4 text-center text-slate-500 text-sm">
                            Enterprise AI Security Red Teaming Platform | Powered by Ada Analytics
                        </div>
                    </footer>
                </div>
            );
        }

        ReactDOM.createRoot(document.getElementById('root')).render(<App />);
    </script>
</body>
</html>"""

# HTML Content - serve FULL_DEMO.html
import os
# main.py is at: distribution/backend/app/main.py
# FULL_DEMO.html is at: distribution/FULL_DEMO.html
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # app -> backend -> distribution
FULL_DEMO = os.path.join(BASE_DIR, "FULL_DEMO.html")

if os.path.exists(FULL_DEMO):
    with open(FULL_DEMO, "r", encoding="utf-8") as f:
        HTML_CONTENT = f.read()
    print(f"[OK] Loaded FULL_DEMO.html from {FULL_DEMO}")
else:
    print(f"[ERROR] FULL_DEMO.html not found at: {FULL_DEMO}")
    HTML_CONTENT = """<!DOCTYPE html>
<html><head><title>Error</title></head>
<body><h1>FULL_DEMO.html not found</h1></body></html>"""

@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the web interface at root"""
    return HTML_CONTENT

@app.get("/ui", response_class=HTMLResponse)
def serve_ui():
    """Serve the web interface"""
    return HTML_CONTENT

@app.get("/api/v1")
def api_root():
    return {
        "message": "API v1",
        "endpoints": ["/api/v1/health", "/api/v1/security-tests", "/api/v1/attack-scenarios", "/api/v1/models"]
    }
