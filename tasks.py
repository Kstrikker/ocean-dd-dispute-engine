"""Celery tasks for evidence extraction and deterministic D&D auditing."""

from __future__ import annotations

import copy
import logging
import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from celery import Celery
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ai_extractor import GEMINI_MODEL, extract_data_with_gemini
from audit_engine import run_deterministic_audit, validate_iso6346
from database import SessionLocal
from models import Container, DayLedgerRow, Document, ExtractionRun, Finding


logger = logging.getLogger(__name__)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "ocean_dd_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    timezone="UTC",
    enable_utc=True,
)


def _load_context(
    db: Session, document_id: uuid.UUID
) -> tuple[Document, ExtractionRun]:
    document = db.scalar(select(Document).where(Document.id == document_id))
    if document is None:
        raise ValueError(f"Document does not exist: {document_id}")

    extraction_run = db.scalar(
        select(ExtractionRun)
        .where(
            ExtractionRun.tenant_id == document.tenant_id,
            ExtractionRun.case_id == document.case_id,
        )
        .order_by(ExtractionRun.created_at.desc())
        .limit(1)
    )
    if extraction_run is None:
        raise ValueError(f"Extraction run does not exist for document: {document_id}")
    return document, extraction_run


def _bind_trusted_context(
    extracted_data: dict[str, Any], document: Document
) -> dict[str, Any]:
    """Bind system-owned IDs without modifying the immutable raw response."""

    validated = copy.deepcopy(extracted_data)
    validated["case_id"] = str(document.case_id)

    for source_document in validated.get("source_documents", []):
        source_document["document_id"] = str(document.id)
    for invoice in validated.get("invoices", []):
        invoice["document_id"] = str(document.id)
    for rule in validated.get("tariff_rules", []):
        rule["document_id"] = str(document.id)
    for evidence in validated.get("field_evidence", []):
        evidence["document_id"] = str(document.id)

    return validated


def _container_for_number(
    db: Session, tenant_id: str, container_number: str
) -> Container:
    normalized = container_number.strip().upper()
    if not validate_iso6346(normalized):
        raise ValueError(
            f"Container cannot enter canonical storage until ISO 6346 passes: "
            f"{normalized}"
        )

    container = db.scalar(
        select(Container).where(
            Container.tenant_id == tenant_id,
            Container.container_number == normalized,
        )
    )
    if container is not None:
        return container

    container = Container(
        tenant_id=tenant_id,
        container_number=normalized,
        iso6346_check_digit_valid=True,
        iso_size_type_code=None,
        length_ft=None,
        height_class=None,
        equipment_category=None,
        ownership=None,
        hazardous=None,
    )
    db.add(container)
    db.flush()
    return container


def _persist_audit_result(
    db: Session,
    *,
    tenant_id: str,
    extraction_run_id: uuid.UUID,
    audit_result: dict[str, Any],
) -> tuple[uuid.UUID, int, int]:
    calculation_run_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"ocean-dd:calculation:{extraction_run_id}",
    )
    containers: dict[str, Container] = {}

    for row in audit_result["ledger_rows"]:
        container_number = str(row["container_number"])
        container = containers.get(container_number)
        if container is None:
            container = _container_for_number(db, tenant_id, container_number)
            containers[container_number] = container

        db.add(
            DayLedgerRow(
                tenant_id=tenant_id,
                calculation_run_id=calculation_run_id,
                container_id=container.id,
                charge_type=str(row["charge_type"]),
                local_date=date.fromisoformat(str(row["local_date"])),
                clock_day_ordinal=int(row["clock_day_ordinal"]),
                eligible_free_day=bool(row["eligible_free_day"]),
                free_day_ordinal=row["free_day_ordinal"],
                impediment_codes=list(row["impediment_codes"]),
                chargeable=bool(row["chargeable"]),
                chargeable_day_ordinal=row["chargeable_day_ordinal"],
                rate_tier_id=None,
                daily_rate=Decimal(str(row["daily_rate"])),
                currency=str(row["currency"]),
                amount=Decimal(str(row["amount"])),
                reason_code=str(row["reason_code"]),
                evidence_ids=list(row["evidence_ids"]),
            )
        )

    for finding in audit_result["findings"]:
        disputed_amount = finding.get("disputed_amount")
        db.add(
            Finding(
                tenant_id=tenant_id,
                compliance_evaluation_id=None,
                calculation_run_id=calculation_run_id,
                reason_code=str(finding["reason_code"]),
                posture=str(finding["posture"]),
                severity=str(finding["severity"]),
                affected_dates=list(finding["affected_dates"]),
                disputed_amount=(
                    Decimal(str(disputed_amount))
                    if disputed_amount is not None
                    else None
                ),
                disputed_currency=finding.get("disputed_currency"),
                status=str(finding["status"]),
                rule_version_ids=list(finding["rule_version_ids"]),
                evidence_ids=list(finding["evidence_ids"]),
            )
        )

    return (
        calculation_run_id,
        len(audit_result["ledger_rows"]),
        len(audit_result["findings"]),
    )


def _mark_failed(document_id: uuid.UUID, error: Exception) -> None:
    try:
        with SessionLocal() as db:
            document, extraction_run = _load_context(db, document_id)
            extraction_run.status = "FAILED"
            extraction_run.completed_at = datetime.now(UTC)
            extraction_run.warnings = [
                *list(extraction_run.warnings or []),
                {
                    "warning_code": "OTHER",
                    "severity": "ERROR",
                    "message": type(error).__name__,
                    "json_pointer": None,
                    "document_id": str(document.id),
                },
            ]
            document.status = "FAILED"
            db.commit()
    except Exception:
        logger.exception(
            "Could not persist task failure state",
            extra={"document_id": str(document_id)},
        )


@celery_app.task(name="process_document")
def process_document(document_id: str, file_path: str) -> dict[str, Any]:
    """Extract evidence, run deterministic audit, and persist results."""

    parsed_document_id = uuid.UUID(document_id)
    path = Path(file_path).resolve(strict=True)

    try:
        with SessionLocal() as db:
            document, extraction_run = _load_context(db, parsed_document_id)
            if extraction_run.status == "READY_FOR_APPROVAL":
                return {
                    "document_id": document_id,
                    "extraction_run_id": str(extraction_run.id),
                    "status": extraction_run.status,
                    "idempotent_replay": True,
                }

            extraction_run.status = "EXTRACTING"
            extraction_run.started_at = datetime.now(UTC)
            document.status = "PROCESSING"
            db.commit()

        raw_extracted_data = extract_data_with_gemini(str(path))

        with SessionLocal() as db:
            document, extraction_run = _load_context(db, parsed_document_id)
            validated_data = _bind_trusted_context(raw_extracted_data, document)
            extraction_run.raw_model_response = raw_extracted_data
            extraction_run.validated_payload = validated_data
            extraction_run.evidence_items = list(
                validated_data.get("field_evidence", [])
            )
            extraction_run.warnings = list(
                validated_data.get("extraction_warnings", [])
            )
            extraction_run.model_version = GEMINI_MODEL
            extraction_run.prompt_version = "evidence-compiler-v1"
            extraction_run.parser_version = (
                "phase-3-mock-v1" if os.getenv("GEMINI_MOCK", "true").lower()
                in {"1", "true", "yes", "on"}
                else "gemini-native-pdf-v1"
            )
            db.commit()

        audit_result = run_deterministic_audit(validated_data)

        with SessionLocal() as db:
            document, extraction_run = _load_context(db, parsed_document_id)
            calculation_run_id, ledger_count, finding_count = _persist_audit_result(
                db,
                tenant_id=document.tenant_id,
                extraction_run_id=extraction_run.id,
                audit_result=audit_result,
            )
            extraction_run.status = "READY_FOR_APPROVAL"
            extraction_run.completed_at = datetime.now(UTC)
            document.status = "READY_FOR_APPROVAL"
            db.commit()

        return {
            "document_id": document_id,
            "extraction_run_id": str(extraction_run.id),
            "calculation_run_id": str(calculation_run_id),
            "ledger_row_count": ledger_count,
            "finding_count": finding_count,
            "status": "READY_FOR_APPROVAL",
        }
    except Exception as exc:
        _mark_failed(parsed_document_id, exc)
        logger.exception(
            "Document processing failed",
            extra={"document_id": document_id},
        )
        raise

