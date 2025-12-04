# NexusCore

NexusCore is the central integration hub that connects APEX (Agentic Processing and EXtraction) with AggreGator, creating a powerful intelligence analysis platform. Recent work focused on delivering high-signal mission briefings and commander-ready decision context directly inside the mission workspace.

## Key Capabilities

- **Templated mission reports** – Analysts can launch configurable LEO case summaries, delta updates, and commander decision sheets with one click. The generator now includes richer template picker cards, inline guardrail posture, and a scrollable, prose-styled HTML preview.
- **Decision intelligence sidebar** – Mission decisions, COAs, blind spots, and policy checks are rendered with severity dots, risk/policy badges, and collapsible detail panes to help commanders evaluate trade-offs quickly.
- **Guardrail + KG context** – Every templated product includes guardrail posture, knowledge-graph snapshots, and blind-spot summaries so stakeholders know what data was—and was not—available.
- **Debug/testing utilities** – Set `NEXT_PUBLIC_SHOW_REPORT_DEBUG=true` to expose the TemplateReportDebugPanel, which surfaces the last request payload and raw TemplateReportResponse for faster troubleshooting.

## Project Structure

```
NexusCore/
├── api/               # API layer for external communication
├── core/              # Core business logic and services
│   ├── apex/         # APEX integration components
│   ├── aggregator/   # AggreGator integration components
│   └── models/       # Shared data models
├── config/           # Configuration files
├── tests/            # Integration and unit tests
└── scripts/          # Utility scripts
```

## Getting Started

1. Clone this repository
2. Set up the development environment
3. Configure the connections to APEX and AggreGator
4. Run the integration services
5. Navigate to any mission and use **Generate intel product** to exercise templated reports. Enable `NEXT_PUBLIC_SHOW_REPORT_DEBUG=true` locally to inspect raw request/response payloads while developing.

## Development

### Prerequisites
- Python 3.9+
- Node.js 16+ (for frontend components)
- Docker (for containerized deployment)

### Installation

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Architecture

NexusCore acts as a middleware that:
1. Coordinates data flow between APEX and AggreGator
2. Provides unified APIs for client applications
3. Handles data transformation and normalization
4. Manages authentication and authorization

## License

[Your License Here]
