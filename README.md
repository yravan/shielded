# Shielded

Geopolitical risk hedging advisory platform. Shielded maps company exposure to geopolitical events tracked by prediction markets (Polymarket, Kalshi, Metaculus) and compares prediction market hedges against traditional financial instruments like FX forwards, oil futures, and sector ETF puts.

## What it does

- **Event Monitoring** — Tracks 8+ geopolitical events (trade wars, conflicts, regulatory changes) with real-time probability data and historical charts
- **Exposure Mapping** — Maps companies' financial exposure (revenue, supply chain, operations) to each event with sensitivity analysis
- **Hedge Comparison** — Side-by-side comparison of prediction market hedges vs traditional instruments, showing cost savings of 15-40%
- **Scenario Analysis** — Models financial impact across probability ranges for each company-event pair

## Tech Stack

| Layer | Tech |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, shadcn/ui v4, Recharts, React Query |
| Backend | FastAPI, SQLAlchemy (async), Pydantic v2, Celery, Redis |
| Database | TimescaleDB (PostgreSQL 16) |
| Infrastructure | Docker Compose |

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) 20+
- [pnpm](https://pnpm.io/) (or enable via `corepack enable && corepack prepare pnpm@latest --activate`)
- [uv](https://docs.astral.sh/uv/) (or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- [PostgreSQL](https://www.postgresql.org/) 16 (or [TimescaleDB](https://www.timescale.com/))
- [Redis](https://redis.io/) 7+
- *(Optional)* [Docker](https://www.docker.com/) and Docker Compose — if you prefer containerized setup

### Frontend Only (with mock data)

The frontend runs standalone with built-in mock data — no backend needed.

```bash
git clone https://github.com/yravan/shielded.git
cd shielded/frontend

# Install dependencies
pnpm install

# Create env file (mock mode is on by default)
cp .env.local.example .env.local
# Or just create it manually:
echo "NEXT_PUBLIC_USE_MOCKS=true" > .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> .env.local

# Start dev server
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) — you'll see the landing page. Click **Get Started** to enter the dashboard.

### Full Stack with Docker

```bash
git clone https://github.com/yravan/shielded.git
cd shielded

# Start backend services (API, database, Redis, Celery)
docker compose up -d

# Run database migrations
docker compose exec api alembic upgrade head

# Seed the database
docker compose exec api python -m app.seed.run

# In a separate terminal, start the frontend
cd frontend
pnpm install
echo "NEXT_PUBLIC_USE_MOCKS=false" > .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> .env.local
pnpm dev
```

### Full Stack without Docker

Install PostgreSQL and Redis locally (macOS example using Homebrew):

```bash
brew install postgresql@16 redis
brew services start postgresql@16
brew services start redis
```

Create the database and user:

```bash
createdb shielded
psql shielded -c "CREATE USER shielded WITH PASSWORD 'shielded';"
psql shielded -c "GRANT ALL PRIVILEGES ON DATABASE shielded TO shielded;"
psql shielded -c "ALTER DATABASE shielded OWNER TO shielded;"
```

Set up the Python backend:

```bash
cd backend
uv venv
uv pip install -r requirements.txt
cp .env.example .env

# Run database migrations
uv run alembic upgrade head

# Seed the database
uv run python -m app.seed.run
```

Start the backend services (each in a separate terminal):

```bash
# Terminal 1 — API server
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Celery worker
cd backend
uv run celery -A celery_app worker --loglevel=info

# Terminal 3 — Celery beat scheduler
cd backend
uv run celery -A celery_app beat --loglevel=info
```

Start the frontend:

```bash
cd frontend
pnpm install
echo "NEXT_PUBLIC_USE_MOCKS=false" > .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" >> .env.local
pnpm dev
```

### Verify

Both setups start:
- **API** at [http://localhost:8000](http://localhost:8000)
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **Celery worker + beat** for background polling
- **Frontend** at [http://localhost:3000](http://localhost:3000)

```bash
curl http://localhost:8000/api/health
# {"status":"ok","version":"0.1.0"}

curl http://localhost:8000/api/events
# Returns paginated event JSON
```

### Backend Configuration

Copy the example env file and adjust as needed:

```bash
cd backend
cp .env.example .env
```

Key variables:
| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://shielded:shielded@localhost:5432/shielded` | PostgreSQL connection |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for caching |
| `ENABLE_LIVE_POLLING` | `false` | Enable live prediction market polling |
| `POLYMARKET_API_URL` | `https://clob.polymarket.com` | Polymarket public API (no key needed) |
| `KALSHI_API_KEY` | *(empty)* | Optional — enables Kalshi ingestion |
| `METACULUS_API_KEY` | *(empty)* | Optional — enables Metaculus ingestion |

## Project Structure

```
shielded/
├── frontend/                 # Next.js app
│   ├── src/
│   │   ├── app/              # Routes (marketing, dashboard, events, companies, hedging, settings)
│   │   ├── components/       # UI components (layout, charts, events, companies, hedging, shared)
│   │   ├── hooks/            # React Query hooks (use-events, use-companies, use-hedging)
│   │   ├── lib/              # Utilities, mock data
│   │   └── types/            # TypeScript interfaces
│   └── package.json
├── backend/                  # FastAPI app
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── models/           # SQLAlchemy models (Event, Company, Exposure, HedgeAnalysis, ProbabilityHistory)
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic (hedge calculator, impact calculator)
│   │   ├── ingestion/        # Prediction market API clients
│   │   ├── tasks/            # Celery background tasks
│   │   └── seed/             # Database seeder
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── Dockerfile
└── docker-compose.yml        # Full stack orchestration
```

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/events` | List events (filterable by category, status) |
| GET | `/api/events/{id}` | Single event detail |
| GET | `/api/events/{id}/history` | Probability history time series |
| GET | `/api/companies` | List companies |
| GET | `/api/companies/{id}` | Company detail |
| GET | `/api/companies/{id}/exposure` | Company exposure profile |
| GET | `/api/hedge-analysis?company_id=&event_id=` | Hedge comparison |
| GET | `/api/impacts/{company_id}/{event_id}` | Scenario analysis |
