NEXUSCORE ROADMAP (Structured + Prioritized)
(APEX + AggreGator + Local LLM + Templates + Decision Intelligence)
PHASE 0 — Demo Priority (Next 2–3 Days)
Goal: Make NexusCore look intelligent, integrated, and mission-ready.
0.1. Mission-Centric Intelligence Templates (Visible to User)

Why this matters: Gives the illusion of deep domain knowledge fast.

- ✅ OSINT report template (frontend picker + preview wired)
- ✅ HUMINT template
- ✅ GEOINT template
- ✅ SIGINT template
- ✅ LEO Case template (“Case Pack”)
- ✅ Commander decision sheet with blind-spot/policy context
- ✅ Auto-filled sections using the LLM surfaced in the mission page "Generate intel product" flow with prose-styled HTML preview and TemplateReportDebugPanel option

Remaining backend polish: add `_clean_markdown` helper + stricter system prompts in `template_report_service` to keep outputs concise and professional.

0.2. Semantic Profiling + Dataset Annotations (Already Wired—UI Polish)

Recent additions: mission decision context sidebar now exposes blind-spot severity dots, policy/guardrail summaries, and collapsible COAs so semantic annotations translate directly into commander-readable insights.

Make sure the UI clearly displays:

- Column semantics
- Confidence
- Notes
- “Regenerate semantics” button

Investor Demo Angle:
“This system understands your data automatically and begins connecting the dots.”

0.3. Gap Detection (Light version)

Basic version for demo:

Detect missing INTs in the mission

Detect missing time windows

Detect entities with no supporting data

Display “Gaps Panel” with suggested tasks

Investor Demo Angle:
“The system identifies information gaps and tells analysts what to go collect.”

0.4. System Status Widget

Small green/red indicators on top right:

Backend: UP/DOWN

Local LLM: UP/DOWN

AggreGator: UP/DOWN

Investor Demo Angle:
“This is a real distributed intelligence platform.”

0.5. Docker One-Click Boot

Already almost complete — just make sure:

docker compose up -d boots everything

Local LLM accessible

Backend health checks passing

Demo dataset auto-seeded

Investor Demo Angle:
“One-click deployment on any machine—no setup.”

PHASE 1 — Near-Term Engineering (Next 2–3 Weeks)
Goal: Turn NexusCore from “cool demo” into a viable product.
1.1. First-Class Entities (People, Orgs, Locations)

Right now these live in the KG but not as DB objects.

Add:

Person

Organization

Location (with lat/long normalization)

Entity dictionaries

Cross-mission linking (“This person appears in 3 missions”)

Why:
Unlocks mapping, LEO workflows, threat grouping, link analysis.

1.2. Mapping Engine (Basic Version)

Backend:

Normalize locations via geocoder or LLM

Publish mission geo entities via /missions/{id}/geo

Frontend:

Map panel on mission page

Pins for events, entities, sightings

Timeline slider to filter events

Why:
LEOs and customers expect a map. Must exist early.

1.3. Advanced Gap Analysis Engine

Moving beyond the demo version:

For each INT template:
Define expected coverage → time/space/entities

Gap types:

Missing INT channels

Missing entities

Missing spatial coverage

Missing time windows

Inconsistent data between INTs

Conflicts detected (cross-source disagreement)

Backend stores structured “IntelGaps”

Frontend shows gap cards with severity + recommended action

Why:
This becomes your “smart decision” capability.

1.4. Mission “Case Pack” Generator (All INTs Combined)

OSINT + HUMINT + SIGINT + GEOINT

Summary sheet

Timeline

Key entities

Threat score

Recommended actions

Gaps

Appendices

Why:
This becomes your biggest “magic feature.”

1.5. Local LLM Model Store & Management

Implement:

/models/install

/models/delete

/models/set-active

/models/list

Support:

Ollama model installs

Adding custom fine-tuned models

Auto-detect running models

Why:
This sells the platform to enterprise and .gov clients.

PHASE 2 — Mid-Term Expansion (1–3 Months)
Goal: Add real-world operational capability for LEO + federal use.
2.1. LEO-Specific Case Workflow

The “Cases” mode includes:

Case → Persons → Vehicles → Locations

Leads management

Prioritization engine (LLM + rules)

“Next investigative steps” recommendations

Evidence timeline

Legal gates (warrants, policy constraints)

Why:
Becomes a sellable product segment.

2.2. Policy & Authority Reasoning (Title 10/50 / Warrant Requirements)
Backend:

Policy KG

Structured rules (“LEO cannot do X without Y”)

Authority tags per mission

LLM usage:

“Is this recommended action compliant with policy?”

“What alternative action remains legal?”

Why:
Turns NexusCore into an “augmented judgment” engine.

2.3. Realtime Feeds + Sensor Fusion (First Steps)

Support ingestion of:

Camera metadata

ALPR

ShotSpotter-style sensors

Local RMS/CAD exports

OSINT streams (RSS, X, Telegram)

Why:
Real intelligence systems must ingest continuous data.

2.4. Multi-Agent Reasoning Layer

Agents:

Extraction agent

Gaps agent

Collection planning agent

COA generator agent

Cross-source consistency checker

Intel chief agent (“assemble the final report”)

Why:
Creates autonomy + removes human bottlenecks.

PHASE 3 — Long-Term Vision (3–12 Months)
Goal: NexusCore becomes a full-blown Intelligence OS.
3.1. Knowledge Graph 2.0

Cross-mission reasoning

Risk scoring per entity

Relationship strengths

Anomaly detection

Temporal embedding (“behavior over time”)

3.2. Federation Layer

Query across:

Multiple NexusCore nodes

Air-gapped deployments

Field laptops

HQ servers

Cloud clusters

3.3. Predictive Modeling

Based on collected INTs:

Predict locations of future events

Predict behavior of entities

Suggest pattern-of-life summaries

Early warning alerts

PRIORITY SUMMARY (What You Need Right Now)
Immediate demo priorities (2–3 days):

Templates for all INTs

Gap detection (simple version)

Semantic profiling UI polish

System status indicators

Docker one-click deployment

Near-term (next 2–3 weeks):

First-class entities

Mapping

Advanced gap engine

Case Pack generator

Model management

Mid-term (1–3 months):

LEO workflow

Policy reasoning

Data connectors

Multi-agent engine