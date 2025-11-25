# NexusCore TODO

## Immediate Live Production Work
- [x] Extend frontend data layer with authority/INT metadata helpers (`lib/policy.ts`, mission typing)
- [x] Add authority + INT selectors with inline validation to `MissionForm`
- [x] Render authority + INT badges, guardrail alerts, and policy tooltips across mission list/detail/tabs
- [x] Surface guardrail warnings + policy footprints inside AgentSummary, TemplateReportGenerator, and mission reports
- [ ] Wire guardrail-aware Missions API responses into frontend caching/state to avoid double fetches
- [ ] Finish Docker Compose hardening (health checks, GPU syntax already fixed, ensure `docker compose up -d` succeeds reliably)

## AggreGator Mission Brain Integration
- [x] Extend Mission model + schema with `kg_namespace` (default `mission-{mission_id}`) and persist authority/INT metadata
- [x] Create `MissionDocument` ORM/table for fast-ingest sources (file/url/feed/note) with INT tagging + status tracking
- [x] Add mission document upload + URL ingest endpoints (`POST /missions/{id}/documents/upload|url`) that queue AggreGator ingestion
- [x] Implement `aggregator_client.ingest_document()` to push mission documents (with authority/INT metadata) into per-mission namespaces
- [x] Implement `aggregator_client.get_mission_kg_snapshot()` and thread KG snapshots into `mission_context_service`
- [ ] Use KG snapshots inside analytics/report templates (LLM prompt conditioning, guardrail context)
- [x] Build mission "Sources" tab UI: drag/drop upload, URL paste, INT overrides, per-document ingest status
- [x] Display mission KG health/status in UI (namespace ready, last ingest time)

## Plan Understanding & OPORD / Runbook Analysis

- [ ] Support plan-type mission sources (OPORD, WARNO, CONOP, SOC runbook, LEO task plan, training scenario) via `MissionDocument` with `source_kind = "PLAN"`
- [ ] Implement `plan_extraction_service` that:
  - [ ] Detects document type (OPORD / WARNO / CONOP / SOC runbook / LEO plan / other)
  - [ ] Extracts 5W+H structure (who, what, when, where, why, how) and key tasks/phases
  - [ ] Infers assumed authorities and INT usage from plan text (e.g., Title 10 vs 32 vs LEO, SIGINT vs OSINT vs GEOINT)
  - [ ] Identifies explicit constraints, ROE-like limits, and coordination requirements
- [ ] Persist a structured `PlanProfile` per mission (ORM + schema) including:
  - [ ] Plan metadata (type, version, authorship, effective dates)
  - [ ] Extracted 5W+H
  - [ ] Assumed authorities & INT lanes (with confidence)
  - [ ] Key tasks, dependencies, and critical assumptions
- [ ] Thread `PlanProfile` into `mission_context_service` so all analytics/LLM runs see the plan baseline
- [ ] Push plan entities/tasks into AggreGator KG:
  - [ ] Create mission-scoped nodes for key entities, tasks, and locations
  - [ ] Link plan nodes to document nodes using `source_kind = "PLAN"`
- [ ] Build “Plan” panel on the mission page:
  - [ ] Upload/view primary plan document(s)
  - [ ] Show extracted 5W+H + key tasks and assumptions
  - [ ] Show inferred authorities/INTs with guardrail hints
- [ ] Implement “Plan vs Reality” v0:
  - [ ] Compare `PlanProfile` against actual mission INT coverage and KG nodes
  - [ ] Surface gaps (missing INTs, missing tasks, unaddressed assumptions, stale timelines)
  - [ ] Render a “Plan Health” widget (traffic light + short explanation) on the mission overview

## Guardrail, Policy, and INT UX Enhancements
- [ ] Inline guardrail warnings for mission creation errors (authority conflicts, INT lint) beyond MissionForm (e.g., mission edit, template selection)
- [ ] Policy badge components for mission cards + detail headers (leveraging `lib/policy` helpers)
- [ ] Authority-aware template picker (filter + label templates by allowed authorities/INTs)
- [ ] Policy footprint metadata in report generator footers and exported artifacts
- [ ] Authority/INT-aware recommended actions + guardrail explanations inside AgentSummary

## Phase 0 Roadmap (Next 2–3 Days)
- [ ] OSINT intelligence report template (auto-filled sections)
- [ ] HUMINT intelligence report template
- [ ] GEOINT intelligence report template
- [ ] SIGINT intelligence report template
- [ ] LEO Case "Case Pack" template
- [ ] Template dropdown + generation flow on mission page (select template → auto-fill)
- [ ] Semantic profiling UI polish (column semantics, confidence, notes, regenerate button)
- [ ] Gap detection v0 (missing INTs, missing time windows, entities lacking support, suggested tasks panel)
- [ ] System status widget (backend / AggreGator / LLM indicators, top-right)
- [ ] Docker one-click boot (compose up, local LLM reachable, backend health checks passing)

## Phase 1 Roadmap (Next 2–3 Weeks)
- [ ] First-class entities (Person, Organization, Location) stored in DB with cross-mission linking
- [ ] Mapping engine MVP (geocoding + mission geo endpoint + frontend map/timeline)
- [ ] Advanced gap analysis engine (INT coverage models, structured IntelGaps storage + UI)
- [ ] Mission "Case Pack" generator combining all INTs (summary, timeline, threats, gaps, recommended actions)
- [ ] Local LLM model store/management (`/models/install|delete|set-active|list`, Ollama integration)

## Phase 2 Roadmap (1–3 Months)
- [ ] LEO-specific case workflow (cases, leads, prioritization, evidence timeline, legal gates)
- [ ] Policy & authority reasoning engine (policy KG, structured rules, compliant action recommendations)
- [ ] Realtime feeds + sensor fusion ingestion (camera metadata, ALPR, ShotSpotter, RMS/CAD, OSINT streams)
- [ ] Multi-agent reasoning layer (extraction, gaps, collection planning, COA generation, intel chief)

## Phase 3 Roadmap (3–12 Months)
- [ ] Knowledge Graph 2.0 (cross-mission reasoning, risk scores, relationship strengths, anomaly detection, temporal embeddings)
- [ ] Federation layer (cross-node querying across air-gapped deployments, field laptops, HQ servers, cloud)
- [ ] Predictive modeling (location forecasts, behavior predictions, pattern-of-life summaries, early warning alerts)

## Technical Overview Follow-Ups
- [ ] Fix `_resolve_base_url` bug in `config_llm.get_llm_config()` so `/status` LLM health works
- [ ] Ensure AggreGator + LLM base URLs configurable per topology (Docker DNS vs localhost)
- [ ] Expand `/status` to include mission counts + last analysis timestamps (observability)
- [ ] Add structured logging + tracing across APEX ↔ AggreGator ↔ LLM interactions
- [ ] Implement dataset builder wiring to AggreGator `/profile` (inline sources → semantic metadata)
- [ ] Expose richer KG endpoints (entity neighborhood, prioritized entities) for future UI graph panels
- [ ] Plan auth/TLS hardening for non-demo deployments (API keys or OIDC, TLS termination)

## Security & Access Control
- [ ] Implement authentication layer (OIDC or JWT) with roles: ADMIN, ANALYST, VIEW_ONLY, AUDITOR
- [ ] Enforce per-organization / per-tenant mission isolation (org_id on missions, documents, KG namespaces)
- [ ] Add RBAC checks for mission creation, editing vs analysis-only, and authority/INT access controls
- [ ] Centralize secret management for LLM + AggreGator credentials (env indirection + vault pattern)
- [ ] Document "Who can see what and why" policies for investor/customer review packets

## Compliance & Auditability
- [ ] Mission audit log (creation/edit events, authority/INT changes, report generation history)
- [ ] LLM decision log (prompt metadata hashes, KG snapshot references, output hashes per run)
- [ ] Chain-of-custody tracking for mission documents (uploader, ingest timestamp, status changes)
- [ ] Guardrail override logging (who overrode, reason, timestamp)

## AI Evaluation & Regression Safety
- [ ] Build golden mission evaluation set with expected outputs (entities, gaps, guardrail results)
- [ ] Implement LLM regression harness to run golden set and score policy violations, hallucinations, missed entities
- [ ] Support model swap testing across local models (e.g., mistral vs llama3) with comparable metrics
- [ ] Create guardrail stress-test scripts for out-of-lane prompts (Title 10 vs LEO, CT profiling, SIGINT on US persons)
- [ ] Automate reporting of regression metrics before releasing prompt/model changes

## Human-in-the-Loop Approvals
- [ ] Mission approval workflow (pending → approved) for sensitive authorities/INT mixes
- [ ] Report approval workflow (draft/approved states with human sign-off recorded)
- [ ] Explicit guardrail override UI that requires justification and feeds the audit log

## Data Governance & Retention
- [ ] Configurable retention policies per org/mission type (90/180/365 days defaults)
- [ ] Mission archival + deletion flows (soft-delete + optional hard purge of DB rows, documents, KG namespace)
- [ ] Document-level "right to remove" operations that also prune/annotate KG edges
- [ ] Document encryption-at-rest story (storage location, DB/KG encryption settings) and key rotation playbook

## Performance & Sizing Benchmarks
- [ ] Baseline ingest + analysis benchmarks (N missions × M docs) with published latency targets
- [ ] KG namespace sizing limits + alerts (node/edge counts, storage MB thresholds)
- [ ] LLM throughput expectations (max concurrent analyses per hardware profile)
- [ ] Resource dashboards or logs capturing ingest latency and LLM call duration per mission

## Performance & Click-Speed Optimization
- [ ] Run FastAPI in production mode inside Docker (`uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4`, no `--reload`)
- [ ] Reduce backend debug logging in production images unless explicitly enabled
- [ ] Switch frontend container to production builds (`next build` during image build, `next start` at runtime)
- [ ] Add `/warmup` endpoint (LLM ping, AggreGator touch, trivial analysis) and invoke it automatically on container start
- [ ] Allocate additional CPUs/RAM to Docker Desktop Linux VM and set service-level resource reservations/limits in compose to protect LLM + backend
- [ ] Instrument key endpoints with timing middleware (path, duration, mission_id) to surface slow calls
- [ ] Cache mission/policy metadata client-side (SWR/React Query) to avoid redundant `/missions` and metadata fetches
- [ ] Prefetch mission details (authority, INTs, latest analysis) when listing missions for instant tab switches
- [ ] Batch or parallelize mission dashboard API calls (or add single combined endpoint) to eliminate sequential waits
- [ ] Introduce optimistic UI + skeleton loaders for long-running actions (report generation, analysis)
- [ ] Eliminate mission N+1 fetch patterns by passing preloaded data down component trees

## Operator Documentation & Onboarding
- [ ] Operator quickstart guide (mission creation → authority/INT selection → source ingest → report)
- [ ] Authority/INT playbook in plain language to guide mission setup choices
- [ ] Guardrail explanation panel outlining what is blocked, why, and how to stay compliant
- [ ] Internal runbook for troubleshooting Docker stack, AggreGator ingest, LLM failures

## Extensibility & Integrations
- [ ] Define ingestion connector interface (RMS, CAD, ALPR, OSINT feeds) with documentation + examples
- [ ] Plan action plugin interface for future tasking/COA integrations while keeping core isolated
- [ ] Publish guidance on adding new INT pipelines or KG processors without modifying core services

## Frontend UX + System Polish
- [ ] Mission list/detail performance tuning (pagination, skeletons, caching)
- [ ] Frontend error boundaries + toasts for ingest/analyze/report actions
- [ ] System status bar hooked into `/status` polling with inline alerts
- [ ] Ensure mission deletion clears KG namespace + documents (once KG integration lands)
- [ ] Document UI/UX guidelines for authority-aware styling to keep consistency
