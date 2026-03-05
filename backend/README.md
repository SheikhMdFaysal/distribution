# Enterprise AI Security Red Teaming Platform - Backend

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.template .env
# Edit .env with your API keys
```

3. Initialize database:
```bash
# PostgreSQL must be running
python -c "from app.models.database import init_db; init_db()"
```

4. Seed attack scenarios:
```bash
python -c "
from app.models.database import get_session_local, init_db
from app.seed_data import seed_attack_scenarios
init_db()
SessionLocal = get_session_local()
db = SessionLocal()
seed_attack_scenarios(db)
"
```

5. Start Redis (for job queue):
```bash
redis-server
```

6. Start the application:
```bash
# Terminal 1: Start API
uvicorn app.main:app --reload --port 8000

# Terminal 2: Start RQ worker
python app/workers/model_execution.py
```

7. Access API documentation:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Environment Variables

Copy `.env.template` to `.env` and configure:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key (optional)
- `ANTHROPIC_API_KEY`: Anthropic API key (optional)
- `GOOGLE_API_KEY`: Google API key (optional)

## Testing

Run tests:
```bash
pytest backend/tests/
```

## API Endpoints

- `POST /api/v1/security-tests/run` - Create and run a security test
- `GET /api/v1/security-tests` - List all tests
- `GET /api/v1/security-tests/{id}` - Get test details
- `GET /api/v1/security-tests/{id}/status` - Get test status
- `GET /api/v1/attack-scenarios` - List attack scenarios
- `POST /api/v1/variants/generate` - Generate style variants
- `GET /api/v1/analytics/dashboard` - Get dashboard analytics
- `GET /api/v1/health` - Health check
