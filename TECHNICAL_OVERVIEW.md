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

## Current Status (Nov 19, 2025)
- ✅ **Phase 1 complete.** Mission datasets now carry `semantic_profile`, the SemanticProfiler service + API endpoint persist LLM-derived annotations, and the frontend renders/refreshes column semantics per dataset.
- ✅ **Phase 2 complete.** `GapAnalysisService`, `/missions/{id}/analysis/gaps`, and the `GapsPriorities` UI deliver structured gaps, priorities, and regeneration controls, cached on missions.
- ✅ **Phase 3 backend + mission experience online.** Template configs live in `app/templates/report_templates.json`, `ReportTemplateEngine` powers `/reports/templates` + `POST /missions/{id}/reports`, and the mission UI now includes `TemplateReportPanel` + `TemplateReportGenerator` for ad-hoc rendering alongside the new policy-aware `GapAnalysisPanel` that uses `POST /missions/{id}/gap_analysis`.
- ✅ **Operational UX polish underway.** Mission detail pages now use a tabbed layout (Overview/Data/Analysis/Reports) plus a live `SystemStatusBar` that surfaces backend/AggreGator/LLM health. Dedicated report-page UX + exports remain open, along with future Phases 4–6.
- ⚠️ **Phase 3 report-page UX + exports still pending.** Need to surface template selection/results on the dedicated report page, add persistence/export hooks, and extend templates set. Decision-support, LEO packaging, and broader ops polish continue to be tracked in Phases 4–6.

## Current End-to-End Flow
1. **Mission creation & context build** – Operator registers a mission (authority, domains, docs, datasets). Mission context service unifies mission, docs, entities, events, and datasets for downstream LLM calls.
2. **Data onboarding** – Operator posts datasets via `/missions/{id}/datasets` with inline source specs. `DatasetBuilderService` (when wired) will proxy those specs to AggreGator `/profile`, and today profiles + semantic profiles reside on each dataset for UI/LLM use.
3. **Agentic analysis** – `RunAnalysisButton` triggers backend agents. Gap analysis can be regenerated via `GET /missions/{id}/analysis/gaps?force_regen=true` (legacy KG flavor) or with the new rule-based + LLM workflow via `POST /missions/{id}/gap_analysis`, which produces `GapAnalysisResult` objects feeding both the backend cache and the mission UI.
4. **Template-driven reporting** – Mission operators fetch available templates (`GET /reports/templates?mission_id=...`) and render policy-aware intel products through `TemplateReportPanel` (JSON view) or `TemplateReportGenerator` (sectioned LLM output built via `POST /missions/{id}/reports/from_template`).
5. **Mission command center UI** – The mission detail page now presents:
   - `SystemStatusBar` (Backend, AggreGator, LLM health via `/status`).
   - Tabbed sections: Overview (MissionDetail, agent + guardrails), Data (documents + datasets), Analysis (GapsPriorities, GapAnalysisPanel, Entities/Events), Reports (TemplateReportPanel + generator).
   - All tabs share the same fetched mission payload so navigation is instant and keeps context consistent during ops.
6. **NexusCore orchestration** – External orchestrators use the same contracts (missions, datasets, template + gap endpoints) to seed missions, build datasets, and dispatch reports, ensuring parity between manual UI workflows and automated runs.

## Roadmap / TODO

This section tracks the staged build-out of NexusCore as a decision-support platform that fuses:

- AggreGator’s data fabric + knowledge graph
- APEX’s mission-centric agentic analysis
- Local LLMs (Ollama) for intel reasoning, gap detection, and planning

### Phase 1 – Mission datasets + KG integration (foundation)

**Goals**

- Treat AggreGator as the single source of truth for profiles + knowledge graph.
- Make APEX agentic analysis aware of datasets and KG context, not just raw documents.

**Tasks**

1. [x] **MissionDataset enrichment** — `semantic_profile` column + schema landed in `models/__init__.py` and Pydantic DTOs, storing alongside AggreGator `profile`.
2. [x] **KG access from APEX** — `services/kg_client.py` wraps AggreGator KG endpoints with helpers for graph, neighborhood, metrics, etc.
3. [x] **Semantic profiling endpoint** — `POST /missions/{mission_id}/datasets/{dataset_id}/semantic_profile` invokes `SemanticProfiler` (LLM-backed) and persists responses.
4. [x] **Frontend hooks** — `MissionDatasetList` shows semantic annotations per column and exposes a “Generate semantic profile” action per dataset.

---

### Phase 2 – KG-aware gap analysis and priorities

**Goals**

- Use the KG and mission datasets to identify **what’s missing**, **what’s conflicting**, and **what’s most important**.
- Make this available as clean JSON that the frontend and export/report flows can consume.

**Tasks**

1. [x] **Gap analysis service (backend)** — `gap_analysis_service.py` fuses KG summaries, datasets, semantic profiles, and (optionally) LLM conflict checks into normalized gap arrays.
2. [x] **Gap analysis endpoint** — `GET /missions/{mission_id}/analysis/gaps` caches results on the mission model and supports `force_regen` for fresh runs.
3. [x] **Priority entities / events** — service now returns `priorities.entities`, `priorities.events`, and a rationale string alongside gap findings.
4. [x] **Frontend gap view** — the mission page renders `GapsPriorities` with refresh controls and sections for missing data, timeline gaps, conflicts, unknowns, quality findings, and priorities.

---

### Phase 3 – Intel product templates (report generation)

**Goals**

- Turn the analysis + KG + datasets into **repeatable, named intel products**, not free-form LLM paragraphs.
- Support multiple template types (ISR, cyber, LEO, etc.).

**Tasks**

1. [x] **Template config model** — JSON configs live in `backend/app/templates/report_templates.json` (e.g., `pattern_of_life`, `incident_readout`).
2. [x] **Template engine (backend)** — `ReportTemplateEngine` aggregates mission/doc/dataset/gap context and renders each template section via `LLMClient` with fallback stubs.
3. [x] **Template endpoints** — `/reports/templates` enumerates configs, and `POST /missions/{mission_id}/reports?template=...` returns rendered sections + metadata.
4. [ ] **Frontend report UX** — Mission page now embeds `TemplateReportGenerator` + `TemplateReportPanel`, but the dedicated “Report” page still needs template selection, stable section layouts, and export options.

---

### Phase 4 – Decision-support & COA planning

**Goals**

- Move from “describe the situation” to **“help decide what to do next.”**
- Support different decision frames (ISR, cyber, LEO casework, etc.).

**Tasks**

1. **Decision engine service**
   - Add `DecisionSupportService` that:
     - Reads gap analysis, priorities, and mission objectives.
     - Calls `LLMClient` to generate:
       - Courses of Action (COAs).
       - Pros/cons and risk scores.
       - Recommended COA with justification.

2. **Decision endpoints**
   - `POST /missions/{mission_id}/decisions/coa`
   - Optional payload to specify:
     - Time pressure (low/med/high).
     - Rules of engagement / constraints.
     - Focus entity or area.

3. **Frontend decision panel**
   - “Decision Support” card on the mission page:
     - List COAs.
     - Show risk/benefit summary.
     - Clearly separate “AI suggestion” from human authority.

4. **Use-case profiles**
   - Add the concept of a “use-case profile” (ISR, cyber, LEO).
   - Profiles influence:
     - Which templates are available.
     - How gap analysis and decision prompts are phrased.
     - Which KG schemas/fields are emphasized.

---

### Phase 5 – LEO-focused packaging and UX

**Goals**

- Make NexusCore feel like a purpose-built **investigative assistant** for local law enforcement.
- Reuse the same core engine with different templates and labels.

**Tasks**

1. **LEO schema & KG extensions**
   - Define LEO-relevant entity/edge types (case, suspect, victim, location, incident, gang, POI).
   - Extend AggreGator KG mapping to support LEO data sources (CAD exports, RMS, OSINT).

2. **LEO intel templates**
   - Examples:
     - Case summary
     - POI timeline
     - Crime series correlation
     - Gang network overview
     - Warrant-support narrative (with clear disclaimers)

3. **Role-based UX**
   - Simple “Detective view” with:
     - Case list
     - Linked entities/locations
     - AI-generated “Where to look next” suggestions.

4. **Policy / compliance hooks (future)**
   - Hooks for audit logging and usage justification.
   - Guardrails for prohibited use cases based on department policy.

---

### Phase 6 – Ops / observability / polish

**Goals**

- Make the stack easy to deploy, monitor, and demo.

**Tasks**

1. **Health & status surfaces**
   - Expand `/status` payload to include:
     - KG connectivity
     - Template registry status
     - Most recent analysis timestamps.

2. [x] **Frontend status indicators**
   - Mission detail page now shows `SystemStatusBar` (Backend / AggreGator / LLM) refreshed every 15 s, matching the `/status` endpoint payload.

3. **Docker & one-click demo**
   - Keep docker-compose stack aligned with:
     - Ollama models
     - AggreGator backend
     - APEX backend + frontend
   - Provide a minimal “demo dataset + mission” seed so investors/LEOs can see value immediately.
