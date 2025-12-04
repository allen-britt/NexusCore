from __future__ import annotations

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.db.session import Base
from app.services.evidence_extractor_service import EvidenceExtractorService


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


def test_evidence_extractor_returns_structured_bundle(db_session: Session) -> None:
    mission = models.Mission(
        name="Test Mission",
        description="Sample",
        mission_authority="LEO",
    )
    db_session.add(mission)
    db_session.commit()
    db_session.refresh(mission)

    doc = models.Document(mission_id=mission.id, title="Report", content="Details")
    db_session.add(doc)

    entity = models.Entity(mission_id=mission.id, name="John Doe", type="PERSON", description="Suspect")
    db_session.add(entity)

    event = models.Event(
        mission_id=mission.id,
        title="Burglary",
        summary="Break-in at warehouse",
        timestamp=datetime(2025, 5, 1, 12, 0, 0),
        location="Warehouse",
    )
    db_session.add(event)
    db_session.commit()

    extractor = EvidenceExtractorService(session=db_session)
    bundle = extractor.build_evidence_bundle(mission.id)

    assert bundle.mission_id == str(mission.id)
    assert bundle.mission_name == mission.name
    assert len(bundle.documents) == 1
    assert len(bundle.subjects) == 1
    assert len(bundle.events) == 1
    assert len(bundle.incidents) == 1
