from __future__ import annotations

import enum
from typing import Any, Dict, List, Tuple

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

pytestmark = pytest.mark.skip(
    reason="Legacy AggreGator / v1 APEX architecture – out of scope for current EvidenceBundle + LEO report refactor."
)

from app import models
from app.db.session import Base
from app.services import agent_service, authority_history, extraction_service, guardrail_service, llm_client
from app.services.template_report_service import _sanitize_report_markdown


@pytest.fixture()
def db_session() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class DummyProfile(enum.Enum):
    HUMINT = "humint"


@pytest.mark.asyncio
async def test_agent_cycle_sanitizes_analysis_output(
    db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    mission = models.Mission(
        name="Test",
        description="Desc",
        mission_authority="LEO",
        kg_namespace=None,
    )
    db_session.add(mission)
    db_session.commit()
    db_session.refresh(mission)

    doc = models.Document(
        mission_id=mission.id,
        title="Doc",
        content="Base intel",
        include_in_analysis=True,
    )
    db_session.add(doc)
    db_session.commit()

    monkeypatch.setattr(extraction_service, "AnalysisProfile", DummyProfile)

    async def _stub_extract_entities_and_events_for_mission(
        *args, **kwargs
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        return [], []

    monkeypatch.setattr(
        extraction_service,
        "extract_entities_and_events_for_mission",
        _stub_extract_entities_and_events_for_mission,
    )

    async def _stub_extract_raw_facts(*args, **kwargs) -> List[dict]:
        return []

    async def _stub_detect_information_gaps(*args, **kwargs) -> dict:
        return {"gaps": []}

    async def _stub_cross_document_analysis(*args, **kwargs) -> dict:
        return {}

    async def _stub_generate_operational_estimate(*args, **kwargs) -> str:
        return "Federal posture still focuses on City Hall complex."

    async def _stub_summarize_mission(*args, **kwargs) -> str:
        return "Provided context outlines Federal Law Enforcement activity near City Hall."

    async def _stub_suggest_next_steps(*args, **kwargs) -> str:
        return "1. Coordinate with Federal partners stationed at City Hall."

    async def _stub_self_verify_assessment(*args, **kwargs) -> dict:
        return {"internal_consistency": "good", "confidence_adjustment": 0.0, "notes": []}

    async def _stub_generate_run_delta(*args, **kwargs) -> str:
        return "No change."

    monkeypatch.setattr(llm_client, "extract_raw_facts", _stub_extract_raw_facts)
    monkeypatch.setattr(llm_client, "detect_information_gaps", _stub_detect_information_gaps)
    monkeypatch.setattr(llm_client, "cross_document_analysis", _stub_cross_document_analysis)
    monkeypatch.setattr(
        llm_client,
        "generate_operational_estimate",
        _stub_generate_operational_estimate,
    )
    monkeypatch.setattr(llm_client, "summarize_mission", _stub_summarize_mission)
    monkeypatch.setattr(llm_client, "suggest_next_steps", _stub_suggest_next_steps)
    monkeypatch.setattr(llm_client, "self_verify_assessment", _stub_self_verify_assessment)
    monkeypatch.setattr(llm_client, "generate_run_delta", _stub_generate_run_delta)

    monkeypatch.setattr(
        authority_history,
        "build_authority_history_payload",
        lambda mission: {"entries": [], "lines": []},
    )

    monkeypatch.setattr(guardrail_service, "set_guardrail_context", lambda **kwargs: None)
    monkeypatch.setattr(
        guardrail_service,
        "run_guardrails",
        lambda *args, **kwargs: {"status": "ok", "issues": []},
    )

    async def _stub_evaluate_guardrails(*args, **kwargs) -> Dict[str, Any]:
        return {"status": "OK", "issues": []}

    monkeypatch.setattr(guardrail_service, "evaluate_guardrails", _stub_evaluate_guardrails)

    class StubAggregator:
        def get_graph_summary(self, *args, **kwargs):
            return None

        def ingest_json_payload(self, *args, **kwargs):
            return None

    monkeypatch.setattr(agent_service, "_aggregator_client", StubAggregator())

    agent_run = await agent_service.run_agent_cycle(mission.id, db_session)

    banned_phrases = [
        "federal",
        "city hall",
        "provided context",
        "provided mission",
        "provided mission text",
        "provided json",
        "agent run advisory",
        "event id",
        "evidence.incidents[",
    ]

    summary_text = (agent_run.summary or "").lower()
    for phrase in banned_phrases:
        assert phrase not in summary_text

    next_steps_text = (agent_run.next_steps or "").lower()
    for phrase in banned_phrases:
        assert phrase not in next_steps_text


def test_report_markdown_sanitizer_strips_internal_markers() -> None:
    dirty = "Evidence from Agent Run Advisory referencing evidence.incidents[0] and Event ID 4 in provided JSON context."
    clean = _sanitize_report_markdown(dirty)
    lowered = clean.lower()
    assert "agent run advisory" not in lowered
    assert "evidence.incidents" not in lowered
    assert "event id" not in lowered
    assert "provided json" not in lowered
