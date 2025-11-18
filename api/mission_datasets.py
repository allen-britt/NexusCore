"""Mission dataset API routes."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.session import get_db
from app.services.dataset_builder_service import DatasetBuilderService


router = APIRouter(prefix="/missions/{mission_id}/datasets", tags=["mission_datasets"])


def get_builder_service() -> DatasetBuilderService:
    return DatasetBuilderService()


def _get_mission_or_404(mission_id: int, db: Session) -> models.Mission:
    mission = db.query(models.Mission).filter(models.Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    return mission


@router.post("", response_model=schemas.MissionDatasetRead, status_code=status.HTTP_201_CREATED)
def create_dataset(
    mission_id: int,
    payload: schemas.MissionDatasetCreate,
    db: Session = Depends(get_db),
    builder: DatasetBuilderService = Depends(get_builder_service),
) -> schemas.MissionDatasetRead:
    _get_mission_or_404(mission_id, db)
    profile = builder.build_dataset_profile(payload.sources)

    dataset = models.MissionDataset(
        mission_id=mission_id,
        name=payload.name,
        status="ready",
        sources=payload.sources,
        profile=profile,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@router.get("", response_model=List[schemas.MissionDatasetRead])
def list_datasets(mission_id: int, db: Session = Depends(get_db)) -> List[schemas.MissionDatasetRead]:
    _get_mission_or_404(mission_id, db)
    return (
        db.query(models.MissionDataset)
        .filter(models.MissionDataset.mission_id == mission_id)
        .order_by(models.MissionDataset.created_at.desc())
        .all()
    )


@router.get("/{dataset_id}", response_model=schemas.MissionDatasetRead)
def get_dataset(
    mission_id: int,
    dataset_id: int,
    db: Session = Depends(get_db),
    builder: DatasetBuilderService = Depends(get_builder_service),
) -> schemas.MissionDatasetRead:
    _get_mission_or_404(mission_id, db)
    dataset = (
        db.query(models.MissionDataset)
        .filter(models.MissionDataset.id == dataset_id, models.MissionDataset.mission_id == mission_id)
        .first()
    )
    if not dataset or dataset.mission_id != mission_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return dataset