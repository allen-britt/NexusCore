# NexusCore / AggreGator / APEX – Technical Overview

## Tech Stack Summary

| Layer | Technologies |
| --- | --- |
| Backend (APEX) | FastAPI, SQLAlchemy, Pydantic v2, httpx, PostgreSQL (via SQLAlchemy models), pytest |
| Data Fabric (AggreGator) | FastAPI, DuckDB, Pandas, PyArrow, YAML source registry, Matplotlib, Playbook automation |
| NexusCore Orchestration | Python 3.11 services, Pydantic models, aiohttp/httpx clients linking AggreGator → APEX |
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| Tooling | pnpm, Node 18+, eslint, prettier, dotenv, pytest-asyncio |
| Storage | DuckDB parquet datasets (AggreGator), PostgreSQL (APEX) |

## Top-Level Directory Map
```
Run2/NexusCore/
├─ core/
│  ├─ AggreGator/                  # Fresh clone of allen-britt/AggreGator
│  │  └─ edge-analytics/           # FastAPI app, connectors, dictionary, storage, new /profile endpoint
│  └─ APEX/                        # Fresh clone of allen-britt/APEX
│     ├─ backend/app/              # FastAPI routers, services, schemas
│     └─ frontend/                 # Next.js mission experience
├─ nexuscore/                      # Orchestration clients, AI helpers, services
├─ scripts/                        # Utilities (e.g., future demo ingestion scripts)
├─ TECHNICAL_OVERVIEW.md           # This document
└─ README.md
```

## Integration Notes

1. **AggreGator as data fabric**
   - `edge-analytics/app.py`: orchestrates DuckDB storage, profiling, knowledge graph, streams.
   - `source_registry.py` + `connectors.py`: declarative ingestion from files, APIs, Splunk, SQL, etc.
   - `dictionary.py`: semantic tagging, FK detection, profiling metrics.

2. **APEX as mission brain**
   - `backend/app/models/__init__.py`: Missions, Documents, MissionDatasets, AgentRuns.
   - `backend/app/api/mission_datasets.py`: POST/GET endpoints for mission datasets using DatasetBuilderService.
   - `backend/app/services/dataset_builder_service.py`: will call AggreGator `/profile` for canonical profiling (currently pending wiring in this workspace clone).
   - `frontend/app/missions/[id]/page.tsx`: mission dashboard listing documents, agent status, guardrails, datasets.

3. **NexusCore orchestration**
   - `nexuscore/services/ingestion.py`: `NexusIngestionService` ties AggreGator fetch → AI transformer → APEX ingestion.
   - `nexuscore/core/aggregator/client.py` & `core/apex/client.py`: async HTTP clients with retry/error handling.
   - `nexuscore/core/ai/transformer.py`: SmartTransformer for low/no-code transformations.

4. **Latest integration updates**
   - AggreGator (`core/AggreGator/edge-analytics/app.py`) now exposes `POST /profile` that accepts `{"sources": [{"type": "json_inline", "data": ...}]}` and returns normalized table/column metadata with semantic hints.
   - Upcoming work: APEX `DatasetBuilderService` will forward mission dataset sources to AggreGator `/profile`, store the returned profile on `MissionDataset.profile`, and expose table counts in the mission UI.

## Current Phase-0 Flow
1. Operator registers a mission in APEX.
2. Operator posts mission datasets via `/missions/{id}/datasets` with inline source specs.
3. DatasetBuilderService (future) will proxy to AggreGator `/profile` to keep profiling logic centralized.
4. Mission dataset profile JSON is stored with the record and surfaced via API/Frontend.
5. NexusCore orchestration builds upon the same API contract to automate ingestion paths.

## TODO
1. Wire APEX `DatasetBuilderService.build_dataset_profile` to POST to AggreGator `/profile` (configurable base URL).
2. Update APEX mission dataset creation route to persist the returned profile (status `ready`).
3. Surface profile table counts in the mission UI dataset list.
4. Add a simple NexusCore `scripts/demo_ingest.py` to exercise AggreGator→APEX orchestration end-to-end.
5. Extend AggreGator `/profile` to support additional source types (file, registry) beyond `json_inline`.
