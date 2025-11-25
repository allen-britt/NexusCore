# NexusCore / AggreGator / APEX – Technical Overview (Expanded)

## 1. High-Level Architecture

```
                        ┌─────────────────────────────────────┐
                        │             Operator                │
                        │     (Browser: http://localhost:3000)│
                        └─────────────────────────────────────┘
                                           │
                                           │  HTTP (JSON, fetch)
                                           ▼
                   ┌─────────────────────────────────────────────┐
                   │            APEX Frontend (Next.js)          │
                   │  - Next.js 14 (App Router)                  │
                   │  - React 18, TypeScript, Tailwind           │
                   │  - Runs on :3000                            │
                   │                                             │
                   │  API base URL resolution:                   │
                   │    - SSR: APEX_INTERNAL_API_BASE_URL        │
                   │            → e.g. http://apex-backend:8000  │
                   │    - Browser: NEXT_PUBLIC_APEX_API_BASE_URL │
                   │            → e.g. http://localhost:8000     │
                   └─────────────────────────────────────────────┘
                                           │
                                           │ HTTP (REST / JSON)
                                           ▼
                   ┌─────────────────────────────────────────────┐
                   │            APEX Backend (FastAPI)           │
                   │  - FastAPI, SQLAlchemy, Pydantic v2         │
                   │  - Runs on :8000                            │
                   │  - Routers: missions, documents,            │
                   │    mission_datasets, analysis, agent,       │
                   │    report, settings, status, models         │
                   │                                             │
                   │  Key dependencies:                          │
                   │    - PostgreSQL (missions, docs, runs, …)   │
                   │    - AggreGator (profiling, KG)             │
                   │    - LLM (Ollama)                           │
                   └─────────────────────────────────────────────┘
                        │                 │                 │
                        │                 │                 │
                        │ HTTP            │ HTTP            │ LLM API
                        ▼                 ▼                 ▼
     ┌─────────────────────────┐   ┌───────────────────┐   ┌────────────────────┐
     │   PostgreSQL (APEX)     │   │ AggreGator (API)  │   │   Ollama (LLM)     │
     │ - Mission metadata      │   │ - FastAPI @ :8100 │   │ - :11434           │
     │ - Documents / runs      │   │ - /health         │   │ - /api/chat        │
     │ - MissionDatasets       │   │ - /profile        │   │                    │
     └─────────────────────────┘   │   (profiling/KG)  │   └────────────────────┘
                                   │                   │
                                   │                   │
                                   ▼                   │
                     ┌────────────────────────┐        │
                     │ DuckDB Parquet Storage │        │
                     │  (AggreGator data &    │        │
                     │   knowledge graph)     │        │
                     └────────────────────────┘        │


        ┌────────────────────────────────────────────────────────────────┐
        │                    NexusCore Orchestration                     │
        │  (external Python services / CLI / automation runners)        │
        │                                                                │
        │  - `nexuscore/services/ingestion.py`                           │
        │     → Orchestrates:                                           │
        │        1) Fetch / profile from AggreGator                      │
        │        2) Transform via SmartTransformer / DataDictionary      │
        │        3) Push mission docs/datasets into APEX                 │
        │                                                                │
        │  - `nexuscore/core/aggregator/client.py`                       │
        │     base_url: http://localhost:8100  (host-mode default)       │
        │                                                                │
        │  - `nexuscore/core/apex/client.py`                             │
        │     base_url: http://localhost:8000  (host-mode default)       │
        └────────────────────────────────────────────────────────────────┘
```

## 2. Tech Stack (Detailed)

| Layer | Technologies / Details |
| --- | --- |
| Frontend (APEX) | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Node 18, fetch-based API client (`lib/api.ts`). |
| Backend (APEX) | FastAPI, SQLAlchemy, Pydantic v2, httpx, PostgreSQL, pytest / pytest-asyncio. |
| Data Fabric | AggreGator: FastAPI, DuckDB, Pandas, PyArrow, YAML source registry, Matplotlib, NL→SQL, playbooks, KG. |
| NexusCore Orchestration | Python 3.11+, Pydantic, aiohttp/httpx clients, Pandas. Bridges AggreGator → APEX. |
| LLM | Ollama (local) with `mistral`/`phi3` via Ollama chat API. |
| Storage | PostgreSQL (missions, docs, agent runs, datasets); DuckDB/parquet (AggreGator data + KG). |
| Tooling | pnpm / npm, Node 18+, Docker & docker-compose, uvicorn, dotenv, pytest-asyncio, Python logging. |
| Deployment | Docker images for Ollama, AggreGator, APEX backend, APEX frontend; `docker-compose` for one-click demo. |

## 3. Runtime Topologies

### 3.1 Docker Demo Stack (recommended)

`docker-compose.yml` launches:

- Ollama → `11434:11434`
- AggreGator → `8100:8100`
- APEX backend → `8000:8000`
- APEX frontend → `3000:3000`

Internal network contracts:

- Frontend → Backend (SSR): `http://apex-backend:8000`
- Backend → AggreGator: `http://aggregator:8100`
- Backend → LLM: `http://ollama:11434`

Host access:

- Browser → Frontend: `http://localhost:3000`
- Frontend (browser bundle) → Backend: `http://localhost:8000`
- Backend reaches AggreGator / LLM via container DNS names (`aggregator`, `ollama`).

### 3.2 Local Development (no Docker)

Recommended services:

- APEX backend → `http://localhost:8000`
- AggreGator → `http://localhost:8100`
- Ollama → `http://localhost:11434`
- APEX frontend (`npm run dev`) → `http://localhost:3000`

Minimum environment variables:

**Frontend `.env.local`:**

```
NEXT_PUBLIC_APEX_API_BASE_URL=http://localhost:8000
APEX_INTERNAL_API_BASE_URL=http://localhost:8000
```

**Backend (APEX):**

```
AGGREGATOR_BASE_URL=http://localhost:8100
LLM_MISTRAL_URL=http://localhost:11434
LLM_PHI3_URL=http://localhost:11434
# DATABASE_URL, SECRET_KEY, etc.
```

## 4. Core Integration Flows

### 4.1 Mission-Centric Flow

1. **Mission creation (APEX)**
   - Operator creates a mission via frontend → `/missions` (APEX backend).
   - Backend persists mission, metadata, and timestamps in PostgreSQL.

2. **Data onboarding & profiling**
   - Operator adds datasets via `/missions/{id}/datasets` with inline source specs or references.
   - `DatasetBuilderService` (planned wiring) calls AggreGator `/profile` with payloads such as `{"sources": [{"type": "json_inline", "data": ...}]}`.
   - AggreGator returns table/column profiles, semantic metadata, and potential foreign keys.
   - APEX stores raw profile + `semantic_profile` (LLM-derived or rule-based). Frontend renders annotations per column with re-profiling controls.

3. **Analysis & gap detection**
   - Operator triggers analysis via `RunAnalysisButton` / gap analysis actions.
   - APEX uses mission context (docs, datasets, semantic profiles, KG) plus Ollama-backed services to extract facts, detect conflicts, and surface gaps.
   - Results become `GapAnalysisResult` objects exposed via:
     - `GET /missions/{id}/analysis/gaps` (legacy flavor)
     - `POST /missions/{id}/gap_analysis` (rule-based + LLM)

4. **Reporting**
   - Template configs live in `backend/app/templates/report_templates.json` (e.g., `pattern_of_life`, `incident_readout`).
   - `ReportTemplateEngine` aggregates mission context and runs sections through the LLM.
   - Endpoints:
     - `GET /reports/templates?mission_id=...`
     - `POST /missions/{id}/reports?template=...`
   - Frontend surfaces outputs via `TemplateReportPanel` and `TemplateReportGenerator` (future export hooks planned).

5. **NexusCore orchestration**
   - `nexuscore/services/ingestion.py` automates AggreGator fetch → SmartTransformer/DataDictionary transforms → APEX ingestion.
   - Clients:
     - `nexuscore/core/aggregator/client.py` (default `http://localhost:8100`)
     - `nexuscore/core/apex/client.py` (default `http://localhost:8000`)

## 5. Health & Status Path

### 5.1 `/status` endpoint

- Implemented in `backend/app/api/status.py`.
- Response shape:

```json
{
  "overall": "ok" | "degraded",
  "backend": "ok",
  "aggregator": "ok" | "error",
  "llm": "ok" | "error"
}
```

- Health checks:
  - Backend: implicit (request handled).
  - AggreGator: `GET {AGGREGATOR_BASE_URL}/health`.
  - LLM: trivial "Say OK" chat via `LLMClient`.
- Frontend polls via `fetchSystemStatus()` to render `SystemStatusBar` on mission pages.

### 5.2 Known LLM config issue

- `config_llm.get_llm_config()` currently calls `_resolve_base_url()`, which is undefined → `NameError` when config is accessed (`is_demo_mode()` and others).
- **Fix recommendation:** implement `_resolve_base_url()` or inline logic so that:
  - Local Ollama usage derives `base_url` from the active `LocalLlmModel` (`LLM_MISTRAL_URL` / `LLM_PHI3_URL`).
  - Optional override: `APEX_LLM_BASE_URL` for OpenAI-style endpoints.

## 6. Value-Add: Contracts & Gotchas

### 6.1 Contract table

| Concern | Where Set | Docker Value | Host Dev Value |
| --- | --- | --- | --- |
| APEX SSR → Backend | `APEX_INTERNAL_API_BASE_URL` (frontend env) | `http://apex-backend:8000` | `http://localhost:8000` |
| Browser → Backend | `NEXT_PUBLIC_APEX_API_BASE_URL` | `http://localhost:8000` | `http://localhost:8000` |
| Backend → AggreGator | `AGGREGATOR_BASE_URL` | `http://aggregator:8100` | `http://localhost:8100` |
| Backend → LLM | `LLM_MISTRAL_URL`, `LLM_PHI3_URL` | `http://ollama:11434` | `http://localhost:11434` |
| LLM active model | `APEX_ACTIVE_LLM_MODEL` (optional) | `mistral` or `phi3` | same |

### 6.2 Common failure modes

1. **Frontend calls itself instead of backend**
   - Symptom: `/missions` requests hit `http://localhost:3000/missions` → 404.
   - Cause: `NEXT_PUBLIC_APEX_API_BASE_URL` unset.
   - Fix: configure `.env.local` as above.

2. **Backend `/status` shows AggreGator error**
   - Symptom: `aggregator: "error"`, `overall: "degraded"`.
   - Cause: AggreGator down or wrong `AGGREGATOR_BASE_URL`.
   - Fix: start AggreGator or adjust env.

3. **Backend `/status` shows LLM error**
   - Causes: Ollama not running, missing model pull, or `_resolve_base_url` bug.
   - Fix: start Ollama, pull models, patch config logic.

4. **NexusCore orchestration cannot reach services**
   - Symptom: connection refused from NexusCore runner.
   - Cause: running inside container but using `localhost` URLs.
   - Fix: use Docker DNS (`apex-backend`, `aggregator`).

## 7. Future Enhancements (Optional)

### Security

1. Introduce auth between frontend ↔ backend (API keys or OIDC) for non-demo deployments.
2. Add TLS termination via Nginx / Traefik / cloud LB.

### Observability

1. Expand `/status` with last-analysis timestamps and mission counts.
2. Add structured logging + traces (OpenTelemetry) for cross-service flows.

### Scalability

1. Split AggreGator into read-only vs write-heavy instances if necessary.
2. Add worker queue for long-running analyses/report generation.

### Profile & KG Surfacing

1. Expose richer KG endpoints in APEX (via `kg_client`) for UI queries such as:
   - "Show graph neighborhood for entity X"
   - "Highlight entities involved in top N prioritized gaps"
2. Extend UI to visualize KG neighborhoods and prioritized entities.

