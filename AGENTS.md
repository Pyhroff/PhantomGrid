# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Active Project: PhantomGrid (PSBs Hackathon 2026)

This workspace is primarily the **PhantomGrid** deliverables for Person 3 (analyst dashboard + integration tests + threat model). The backend (FastAPI) is owned by Person 2 and runs separately.

### Running tests

```bash
# from workspace root — phantomgrid.db must exist here (created by the backend)
pytest tests/ -v
```

Tests auto-skip if `http://localhost:8000/docs` is unreachable. The session fixture in `conftest.py` enrolls `test_user` once before all tests — no manual setup needed.

### Central config

`config.py` is the single source of truth for all scripts and tests:

```python
BASE_URL = "http://localhost:8000"   # change to ngrok/Railway URL before demo
DEMO_USER = "demo_user"
```

### Opening the dashboard

Open `dashboard/index.html` directly in a browser — no build step. Pass `?user_id=demo_user` in the URL (e.g. `file:///…/dashboard/index.html?user_id=demo_user`). It polls `GET /risk/composite?user_id=…` every 2 s. The backend must have CORS enabled (see `INTEGRATION_NOTES.md`).

## PhantomGrid Architecture

Three-layer behavioral biometrics engine with composite risk fusion:

| Layer | Signal | Enroll endpoint | Score endpoint |
|-------|--------|-----------------|----------------|
| Layer 1 | Decoy interactions, hover hesitation, familiar-zone latency | `POST /enroll/layer1` | `POST /score/layer1` |
| Layer 2 | Navigation entropy, digit fluency gaps, beneficiary dwell | `POST /enroll/layer2` | `POST /score/layer2` |
| Layer 3 (RhythmLock) | PIN keypress intervals (ms) | `POST /enroll/layer3` | `POST /score/layer3` |

**Composite fusion** (`POST /risk/composite`): `L1×0.30 + L2×0.40 + L3×0.30`

**Decision thresholds:** green <60 · amber 60–84 · red ≥85

The dashboard reads `breakdown.layer1 / layer2 / layer3` from `/risk/composite`; `GET /sessions?user_id=…&limit=N` populates the session log table (this endpoint is **missing** — Person 2 must implement it).

SQLite DB (`phantomgrid.db`) at the project root is written by the backend after each `/risk/composite` call; `test_session_log_written_after_composite` reads it directly via `sqlite3`.

## Other Sub-projects

### phantom-investigator/

Full AI investigation platform (separate project, not the hackathon deliverable):

- **Backend**: FastAPI + LangGraph agent pipeline (Python 3.11+, `pyproject.toml`)
- **Frontend**: Next.js (`frontend/`)
- **Infrastructure**: Postgres + Neo4j + Redis + MinIO — all via Docker Compose

```bash
cd phantom-investigator
cp .env.example .env          # fill in secrets
docker compose up --build

# backend only (no docker)
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload

# run migrations
alembic upgrade head

# lint / type-check
ruff check app/
mypy app/
```

**LangGraph pipeline** (`app/agents/graph.py`): `collector → entity_extractor → timeline_builder → relationship_mapper → hypothesis → validator → reporter`. All agents are stateless functions over `InvestigationState`. LLM provider is swappable: set `LLM_PROVIDER=openai|anthropic|ollama` in `.env`.

### typing_dj/

See `typing_dj/AGENTS.md` for full details. Quick start: `pip install -r requirements.txt && python main.py` (requires ffmpeg on PATH).

### rag-demo/ and ent-finetune/

Standalone learning scripts — no server. `rag-demo/rag.py` needs `OPENAI_API_KEY`. `ent-finetune/finetune.py` uploads a JSONL dataset and starts an OpenAI fine-tune job.

### explainer.py

Interactive code explainer using Groq (`llama-3.3-70b-versatile`). Requires `GROQ_API_KEY` (prompts if missing). Run: `python explainer.py`.
