from __future__ import annotations

import pytest

from app import models, schemas
from app.models.evidence import EvidenceBundle
from app.services.template_report_service import TemplateReportService
from app.services.template_service import TemplateService


class StubContextService:
    def build_context_for_mission(self, mission: models.Mission) -> dict:
        return {
            "documents": [],
            "entities": [],
            "events": [],
            "datasets": [],
            "gap_analysis": [],
            "kg_snapshot": None,
        }


class StubLLMClient:
    def chat(self, messages):  # pragma: no cover - should never be invoked in this test
        raise AssertionError("LLM should not be called when EvidenceBundle is empty")


def test_leo_report_no_fabrication(monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty bundles must bypass the LLM and emit deterministic sanitized text."""

    template_service = TemplateService()
    context_service = StubContextService()
    llm_client = StubLLMClient()

    service = TemplateReportService(
        db=None,
        template_service=template_service,
        context_service=context_service,
        llm_client=llm_client,
    )

    mission = models.Mission(name="Test Mission", primary_authority="LEO", original_authority="LEO")
    mission.id = 1

    empty_bundle = EvidenceBundle(mission_id=str(mission.id))

    monkeypatch.setattr(service, "_get_mission", lambda mission_id: mission)
    monkeypatch.setattr(service, "_get_evidence_bundle", lambda mission_id: empty_bundle)

    result = service.generate_report(mission_id=mission.id, template_id="leo_case_summary_v1")
    text = (result.get("markdown") or "").lower()

    assert "none available based on current evidence" in text

    forbidden = ["john", "jane", "doe", "acme", "street", "road", "california", "new york", "friday"]
    for word in forbidden:
        assert word not in text, f"Fabricated noun detected: {word}"


def test_full_intrep_response_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    template_service = TemplateService()
    context_service = StubContextService()
    llm_client = StubLLMClient()

    service = TemplateReportService(
        db=None,
        template_service=template_service,
        context_service=context_service,
        llm_client=llm_client,
    )

    mission = models.Mission(name="Mission", primary_authority="TITLE_10_MIL", original_authority="TITLE_10_MIL")
    mission.id = 7
    mission.mission_authority = "TITLE_10_MIL"

    monkeypatch.setattr(service, "_get_mission", lambda mission_id: mission)
    monkeypatch.setattr(service, "_invoke_markdown_llm", lambda *args, **kwargs: "# Test\nBody")
    monkeypatch.setattr(service, "_render_markdown", lambda markdown: "<p>Body</p>")

    result = service.generate_report(mission_id=mission.id, template_id="full_intrep_v1")

    assert result["html"] == "<p>Body</p>"
    assert result["markdown"].startswith("# Test")
    assert "content" not in result

    # Ensure FastAPI response schema accepts the flattened structure
    schemas.TemplateReportGenerateResponse(**result)
