"""High-level ingestion orchestration for NexusCore."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from nexuscore.core.ai import AIDataInterpreter, DataDictionary, SmartTransformer
from nexuscore.core.ai.transformer import TransformationResult
from nexuscore.core.aggregator import AggregatorClient
from nexuscore.core.aggregator.models import DataChunk
from nexuscore.core.apex import ApexClient


@dataclass
class IngestedDocument:
    """Metadata about a document created in APEX."""

    id: int
    title: Optional[str]


@dataclass
class IngestionReport:
    """Result metadata returned by the ingestion workflow."""

    mission_id: int
    documents: List[IngestedDocument] = field(default_factory=list)
    analysis_run: Optional[Dict[str, Any]] = None
    schema_summary: Dict[str, Any] = field(default_factory=dict)
    field_explanations: Dict[str, str] = field(default_factory=dict)
    transform_metadata: Dict[str, Any] = field(default_factory=dict)


class NexusIngestionService:
    """Coordinates AggreGator fetch, AI assist, and APEX ingestion."""

    def __init__(
        self,
        *,
        aggregator_client: AggregatorClient,
        apex_client: ApexClient,
        interpreter: AIDataInterpreter,
        transformer: SmartTransformer,
        data_dictionary: Optional[DataDictionary] = None,
        default_analysis_profile: str = "humint",
    ) -> None:
        self.aggregator = aggregator_client
        self.apex = apex_client
        self.interpreter = interpreter
        self.transformer = transformer
        self.data_dictionary = data_dictionary
        self.default_profile = default_analysis_profile

    async def ingest_aggregator_source_to_mission_dataset(
        self,
        mission_id: int,
        source_key: str,
        dataset_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Profile an AggreGator source and create a MissionDataset in APEX."""

        await self.aggregator.connect()
        await self.apex.connect()

        profile = await self.aggregator.profile_source(source_key)
        dataset_identifier = (
            profile.get("dataset_id")
            or profile.get("id")
            or profile.get("name")
            or source_key
        )

        sources = [
            {
                "type": "aggregator_source",
                "source_key": source_key,
                "aggregator_dataset_id": dataset_identifier,
            }
        ]

        name = dataset_name or source_key

        mission_dataset = await self.apex.create_mission_dataset(
            mission_id=mission_id,
            name=name,
            sources=sources,
            profile=profile,
        )

        return mission_dataset

    async def ingest_source(
        self,
        source_name: str,
        *,
        mission_id: Optional[int] = None,
        mission_name: Optional[str] = None,
        mission_description: Optional[str] = None,
        transform_spec: Optional[Dict[str, Any]] = None,
        auto_analyze: bool = True,
        analysis_profile: Optional[str] = None,
        document_title: Optional[str] = None,
    ) -> IngestionReport:
        """Run the end-to-end ingestion flow for a registry source."""

        analysis_profile = analysis_profile or self.default_profile

        await self.aggregator.connect()
        await self.apex.connect()

        mission_id = await self._ensure_mission(
            mission_id=mission_id,
            mission_name=mission_name,
            mission_description=mission_description,
        )

        chunk = await self.aggregator.fetch_data(source_name)
        schema_summary = await self.interpreter.infer_schema(chunk)
        field_explanations = await self._build_field_explanations(schema_summary)

        transformed_records, transform_meta = await self._apply_transformations(
            chunk, transform_spec
        )

        document_payload = self._build_document_content(
            source_name=source_name,
            schema_summary=schema_summary,
            explanations=field_explanations,
            records=transformed_records,
            metadata=chunk.metadata,
        )

        apex_doc = await self.apex.add_document(
            mission_id=mission_id,
            content=document_payload,
            title=document_title or f"Ingestion - {source_name}",
        )

        analysis_run = None
        if auto_analyze:
            analysis_run = await self.apex.analyze_mission(
                mission_id=mission_id,
                profile=analysis_profile,
            )

        return IngestionReport(
            mission_id=mission_id,
            documents=[
                IngestedDocument(id=apex_doc.get("id"), title=apex_doc.get("title"))
            ],
            analysis_run=analysis_run,
            schema_summary=schema_summary,
            field_explanations=field_explanations,
            transform_metadata=transform_meta,
        )

    async def _ensure_mission(
        self,
        *,
        mission_id: Optional[int],
        mission_name: Optional[str],
        mission_description: Optional[str],
    ) -> int:
        if mission_id is not None:
            try:
                await self.apex.get_mission(mission_id)
                return mission_id
            except Exception:
                pass

        if not mission_name:
            raise ValueError("mission_name is required when mission_id is not provided")

        mission = await self.apex.create_mission(mission_name, mission_description)
        return mission["id"]

    async def _apply_transformations(
        self,
        chunk: DataChunk,
        transform_spec: Optional[Dict[str, Any]],
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        records = chunk.data
        metadata: Dict[str, Any] = {}

        if not records:
            return records, metadata

        df = pd.DataFrame(records)

        if transform_spec:
            result: TransformationResult = await self.transformer.transform(
                df,
                transform_spec,
            )
            metadata = {
                "transform_success": result.success,
                "message": result.message,
            }
            if result.success:
                records = result.transformed_data  # type: ignore[assignment]
            else:
                metadata["error"] = result.message

        return records, metadata

    async def _build_field_explanations(
        self, schema_summary: Dict[str, Any]
    ) -> Dict[str, str]:
        explanations: Dict[str, str] = {}
        for field in schema_summary.get("fields", []):
            name = field.get("name")
            if not name:
                continue
            explanations[name] = await self.interpreter.explain_field(name, field)
        return explanations

    def _build_document_content(
        self,
        *,
        source_name: str,
        schema_summary: Dict[str, Any],
        explanations: Dict[str, str],
        records: List[Dict[str, Any]],
        metadata: Dict[str, Any],
    ) -> str:
        sample = records[:5]
        doc = {
            "source": source_name,
            "metadata": metadata,
            "schema": schema_summary,
            "explanations": explanations,
            "sample_records": sample,
        }
        return json.dumps(doc, indent=2, default=str)

