from __future__ import annotations

from typing import Any, Dict, Iterator, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

pytestmark = pytest.mark.skip(
    reason="Legacy AggreGator / v1 APEX architecture – out of scope for current EvidenceBundle + LEO report refactor."
)

from app import models
from app.api import graph as graph_api
from app.db.session import Base, get_db
from app.main import app
from app.services.kg_client import KgClientError


@pytest.fixture()
def db_session() -> Iterator[Session]:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_get_db(db_session: Session) -> Iterator[None]:
    def _get_db() -> Iterator[Session]:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def _create_mission(db: Session, *, kg_namespace: Optional[str] = "mission-kg") -> models.Mission:
    mission = models.Mission(name="Test Mission", description="testing", kg_namespace=kg_namespace)
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


def test_get_mission_kg_summary_success(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mission = _create_mission(db_session, kg_namespace="mission-123")

    class StubKgClient:
        def __init__(self) -> None:
            self.called_with: list[str] = []

        def get_summary(self, project_id: str) -> Dict[str, Any]:
            self.called_with.append(project_id)
            return {"nodes": 10}

    stub = StubKgClient()
    monkeypatch.setattr(graph_api, "_kg_client", stub)

    response = client.get(f"/missions/{mission.id}/kg/summary")

    assert response.status_code == 200
    assert response.json() == {"nodes": 10}
    assert stub.called_with == ["mission-123"]


def test_get_mission_kg_summary_upstream_failure(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mission = _create_mission(db_session)

    class FailingKgClient:
        def get_summary(self, project_id: str) -> Dict[str, Any]:  # pragma: no cover - simple stub
            raise KgClientError("boom")

    monkeypatch.setattr(graph_api, "_kg_client", FailingKgClient())

    response = client.get(f"/missions/{mission.id}/kg/summary")

    assert response.status_code == 502
    assert response.json()["detail"] == "Failed to fetch mission KG summary"


def test_neighborhood_requires_node_id(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mission = _create_mission(db_session)

    class StubKgClient:
        def get_neighborhood(self, project_id: str, node_id: str, *, hops: int = 2) -> Dict[str, Any]:
            return {"project_id": project_id, "node": node_id, "hops": hops}

    monkeypatch.setattr(graph_api, "_kg_client", StubKgClient())

    response = client.get(
        f"/missions/{mission.id}/kg/neighborhood",
        params={"node_id": "node-42", "hops": 1},
    )

    assert response.status_code == 200
    assert response.json()["node"] == "node-42"

    missing = client.get(f"/missions/{mission.id}/kg/neighborhood", params={"node_id": ""})
    assert missing.status_code == 400
    assert missing.json()["detail"] == "node_id is required"


def test_suggest_links_forwards_limit(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mission = _create_mission(db_session)

    class StubKgClient:
        def __init__(self) -> None:
            self.calls: list[Dict[str, Any]] = []

        def get_suggested_links(self, project_id: str, *, limit: int = 50) -> Dict[str, Any]:
            self.calls.append({"project_id": project_id, "limit": limit})
            return {"links": []}

    stub = StubKgClient()
    monkeypatch.setattr(graph_api, "_kg_client", stub)

    response = client.get(
        f"/missions/{mission.id}/kg/suggest-links",
        params={"limit": 5},
    )

    assert response.status_code == 200
    assert response.json() == {"links": []}
    assert stub.calls == [{"project_id": mission.kg_namespace, "limit": 5}]


def test_project_id_falls_back_when_namespace_missing(
    client: TestClient,
    db_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mission = _create_mission(db_session, kg_namespace=None)

    class RecordingKgClient:
        def __init__(self) -> None:
            self.project_ids: list[str] = []

        def get_full_graph(
            self,
            project_id: str,
            *,
            limit_nodes: int = 400,
            limit_edges: int = 800,
        ) -> Dict[str, Any]:
            self.project_ids.append(project_id)
            return {"nodes": [], "edges": []}

    stub = RecordingKgClient()
    monkeypatch.setattr(graph_api, "_kg_client", stub)

    response = client.get(f"/missions/{mission.id}/kg/full")

    assert response.status_code == 200
    assert stub.project_ids == [f"mission-{mission.id}"]
