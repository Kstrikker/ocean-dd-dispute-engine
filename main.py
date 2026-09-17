"""FastAPI gateway for document intake and extraction-status polling."""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated

from celery import Celery
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from database import get_db
from models import DayLedgerRow, Document, ExtractionRun, Finding, Tenant


logger = logging.getLogger(__name__)

APP_NAME = "Ocean Freight D&D Dispute Engine"
API_VERSION = "0.2.0"
UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", "/tmp/ocean-dd-uploads"))
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
UPLOAD_CHUNK_BYTES = 1024 * 1024
LOCAL_TENANT_ID = os.getenv("LOCAL_TENANT_ID", "local-dev")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


def _cors_origins() -> list[str]:
    configured = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000,http://localhost:8501",
    )
    return [origin.strip() for origin in configured.split(",") if origin.strip()]


app = FastAPI(
    title=APP_NAME,
    version=API_VERSION,
    description="API gateway for evidence-first ocean-freight D&D processing.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)

# Phase 2 publishes a named task. Phase 3 will register the worker implementation
# under this exact name without changing the gateway contract.
celery_app = Celery("ocean_dd_gateway", broker=REDIS_URL)
process_document = celery_app.signature("process_document")


class UploadResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: uuid.UUID
    document_id: uuid.UUID
    status: str
    message: str


class ExtractionStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    case_id: uuid.UUID
    document_id: uuid.UUID
    extraction_run_id: uuid.UUID
    status: str
    updated_at: datetime


class DayLedgerRowResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    local_date: date
    clock_day_ordinal: int
    eligible_free_day: bool
    free_day_ordinal: int | None
    chargeable: bool
    chargeable_day_ordinal: int | None
    daily_rate: Decimal | None
    amount: Decimal
    currency: str
    reason_code: str
    impediment_codes: list[str]
    evidence_ids: list[str]


class FindingResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID
    reason_code: str
    posture: str
    severity: str
    affected_dates: list[str]
    disputed_amount: Decimal | None
    disputed_currency: str | None
    status: str
    rule_version_ids: list[str]
    evidence_ids: list[str]


class DisputeResultsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: uuid.UUID
    calculation_run_id: uuid.UUID
    invoice_number: str
    container_number: str
    currency: str
    expected_charge: Decimal
    invoiced_charge: Decimal
    variance: Decimal
    ledger_rows: list[DayLedgerRowResponse]
    findings: list[FindingResponse]


def _ensure_local_tenant(db: Session, tenant_id: str) -> Tenant:
    """Resolve the local development tenant without provisioning arbitrary tenants."""

    tenant = db.scalar(select(Tenant).where(Tenant.tenant_id == tenant_id))
    if tenant is not None:
        return tenant

    if tenant_id != LOCAL_TENANT_ID:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found.",
        )

    tenant = Tenant(
        tenant_id=LOCAL_TENANT_ID,
        name="Local Development Tenant",
        status="ACTIVE",
        retention_policy="Development data only; do not upload customer documents.",
    )
    db.add(tenant)
    db.flush()
    return tenant


def _save_pdf(upload: UploadFile, destination: Path) -> str:
    """Persist a bounded PDF upload and return its SHA-256 digest."""

    UPLOAD_DIRECTORY.mkdir(mode=0o700, parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total_bytes = 0
    first_chunk = True

    try:
        with destination.open("xb") as output:
            while chunk := upload.file.read(UPLOAD_CHUNK_BYTES):
                if first_chunk:
                    first_chunk = False
                    if not chunk.startswith(b"%PDF-"):
                        raise HTTPException(
                            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="The uploaded file does not have a valid PDF signature.",
                        )

                total_bytes += len(chunk)
                if total_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"PDF exceeds the {MAX_UPLOAD_BYTES}-byte upload limit.",
                    )

                digest.update(chunk)
                output.write(chunk)
    except Exception:
        destination.unlink(missing_ok=True)
        raise

    if total_bytes == 0:
        destination.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF is empty.",
        )

    return digest.hexdigest()


def _input_fingerprint(
    *, tenant_id: str, case_id: uuid.UUID, document_id: uuid.UUID, sha256: str
) -> str:
    material = f"{tenant_id}:{case_id}:{document_id}:{sha256}:phase-2"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _invoice_context(payload: dict[str, object]) -> tuple[str, str, str, Decimal]:
    """Read extracted invoice identity and totals without recomputing audit logic."""

    invoices = payload.get("invoices")
    if not isinstance(invoices, list) or not invoices:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The validated extraction has no invoice payload.",
        )

    first_invoice = invoices[0]
    if not isinstance(first_invoice, dict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The validated invoice payload is malformed.",
        )

    invoice_number = first_invoice.get("invoice_number")
    if not isinstance(invoice_number, str) or not invoice_number.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The validated extraction has no invoice number.",
        )

    charge_lines: list[dict[str, object]] = []
    for invoice in invoices:
        if not isinstance(invoice, dict):
            continue
        lines = invoice.get("charge_lines")
        if isinstance(lines, list):
            charge_lines.extend(line for line in lines if isinstance(line, dict))

    if not charge_lines:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The validated extraction has no charge lines.",
        )

    container_number = charge_lines[0].get("container_number")
    if not isinstance(container_number, str) or not container_number.strip():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The validated extraction has no container number.",
        )

    currencies: set[str] = set()
    invoiced_charge = Decimal("0")
    for line in charge_lines:
        line_total = line.get("line_total")
        if not isinstance(line_total, dict):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A validated charge line has no line total.",
            )
        amount = line_total.get("amount")
        currency = line_total.get("currency")
        if not isinstance(currency, str) or len(currency) != 3:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A validated charge line has an invalid currency.",
            )
        try:
            invoiced_charge += Decimal(str(amount))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A validated charge line has an invalid monetary amount.",
            ) from exc
        currencies.add(currency.upper())

    if len(currencies) != 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Results cannot aggregate charge lines with mixed currencies.",
        )

    return (
        invoice_number.strip(),
        container_number.strip().upper(),
        currencies.pop(),
        invoiced_charge,
    )


@app.get("/", include_in_schema=False)
def root() -> dict[str, str]:
    return {
        "service": APP_NAME,
        "status": "running",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health", tags=["Operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/upload/",
    response_model=UploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Documents"],
)
def upload_document(
    file: Annotated[UploadFile, File(description="Ocean-freight PDF document")],
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")] = LOCAL_TENANT_ID,
) -> UploadResponse:
    """Store a PDF, create pending records, and enqueue document processing."""

    if file.content_type not in {"application/pdf", "application/x-pdf"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF uploads are accepted.",
        )

    case_id = uuid.uuid4()
    document_id = uuid.uuid4()
    destination = UPLOAD_DIRECTORY / f"{document_id}.pdf"
    display_filename = Path(file.filename or f"{document_id}.pdf").name
    sha256 = _save_pdf(file, destination)

    try:
        _ensure_local_tenant(db, tenant_id)

        document = Document(
            id=document_id,
            tenant_id=tenant_id,
            case_id=case_id,
            document_type="DD_INVOICE",
            display_filename=display_filename,
            status="READY",
            current_version_id=None,
        )
        extraction_run = ExtractionRun(
            tenant_id=tenant_id,
            case_id=case_id,
            status="PENDING",
            schema_version=os.getenv("EXTRACTION_SCHEMA_VERSION", "1.0"),
            model_version="NOT_STARTED",
            prompt_version="NOT_STARTED",
            parser_version="NOT_STARTED",
            ocr_version=None,
            input_fingerprint=_input_fingerprint(
                tenant_id=tenant_id,
                case_id=case_id,
                document_id=document_id,
                sha256=sha256,
            ),
            started_at=datetime.now(UTC),
            completed_at=None,
            supersedes_id=None,
            raw_model_response={},
            validated_payload={},
            evidence_items=[],
            warnings=[],
            layout_snapshot=None,
        )

        db.add_all([document, extraction_run])
        db.commit()
        db.refresh(document)
        db.refresh(extraction_run)
    except HTTPException:
        db.rollback()
        destination.unlink(missing_ok=True)
        raise
    except IntegrityError as exc:
        db.rollback()
        destination.unlink(missing_ok=True)
        logger.warning(
            "Upload metadata conflicted with existing state",
            extra={"document_id": str(document_id), "case_id": str(case_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document metadata conflicts with an existing record.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        destination.unlink(missing_ok=True)
        logger.exception(
            "Database failure during upload registration",
            extra={"document_id": str(document_id), "case_id": str(case_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The document could not be registered.",
        ) from exc

    try:
        process_document.delay(str(document_id), str(destination))
    except Exception as exc:
        extraction_run.status = "ENQUEUE_FAILED"
        document.status = "ENQUEUE_FAILED"
        try:
            db.commit()
        except SQLAlchemyError:
            db.rollback()
            logger.exception(
                "Failed to persist enqueue failure",
                extra={"document_id": str(document_id)},
            )

        logger.exception(
            "Failed to enqueue document",
            extra={"document_id": str(document_id), "case_id": str(case_id)},
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "The document was registered but could not be queued.",
                "case_id": str(case_id),
                "document_id": str(document_id),
            },
        ) from exc

    return UploadResponse(
        case_id=case_id,
        document_id=document_id,
        status="PENDING",
        message="Document accepted and queued for extraction.",
    )


@app.get(
    "/status/{document_id}",
    response_model=ExtractionStatusResponse,
    tags=["Documents"],
)
def get_document_status(
    document_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")] = LOCAL_TENANT_ID,
) -> ExtractionStatusResponse:
    """Return the latest extraction status for an authorized document."""

    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    extraction_run = db.scalar(
        select(ExtractionRun)
        .where(
            ExtractionRun.tenant_id == tenant_id,
            ExtractionRun.case_id == document.case_id,
        )
        .order_by(ExtractionRun.created_at.desc())
        .limit(1)
    )
    if extraction_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extraction run exists for this document.",
        )

    return ExtractionStatusResponse(
        case_id=document.case_id,
        document_id=document.id,
        extraction_run_id=extraction_run.id,
        status=extraction_run.status,
        updated_at=extraction_run.updated_at,
    )


@app.get(
    "/results/{document_id}",
    response_model=DisputeResultsResponse,
    tags=["Documents"],
)
def get_document_results(
    document_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID")] = LOCAL_TENANT_ID,
) -> DisputeResultsResponse:
    """Return persisted deterministic ledger rows and findings for a document."""

    document = db.scalar(
        select(Document).where(
            Document.id == document_id,
            Document.tenant_id == tenant_id,
        )
    )
    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    extraction_run = db.scalar(
        select(ExtractionRun)
        .where(
            ExtractionRun.tenant_id == tenant_id,
            ExtractionRun.case_id == document.case_id,
        )
        .order_by(ExtractionRun.created_at.desc())
        .limit(1)
    )
    if extraction_run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No extraction run exists for this document.",
        )
    if extraction_run.status != "READY_FOR_APPROVAL":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Results are not ready. Current status: {extraction_run.status}.",
        )

    calculation_run_id = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"ocean-dd:calculation:{extraction_run.id}",
    )
    ledger_rows = list(
        db.scalars(
            select(DayLedgerRow)
            .where(
                DayLedgerRow.tenant_id == tenant_id,
                DayLedgerRow.calculation_run_id == calculation_run_id,
            )
            .order_by(
                DayLedgerRow.local_date.asc(),
                DayLedgerRow.clock_day_ordinal.asc(),
            )
        )
    )
    if not ledger_rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No deterministic ledger exists for this document.",
        )

    findings = list(
        db.scalars(
            select(Finding)
            .where(
                Finding.tenant_id == tenant_id,
                Finding.calculation_run_id == calculation_run_id,
            )
            .order_by(Finding.created_at.asc())
        )
    )

    invoice_number, container_number, currency, invoiced_charge = _invoice_context(
        extraction_run.validated_payload
    )
    ledger_currencies = {row.currency.upper() for row in ledger_rows}
    if ledger_currencies != {currency}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ledger and invoice currencies do not match.",
        )

    expected_charge = sum((row.amount for row in ledger_rows), Decimal("0"))
    variance = invoiced_charge - expected_charge

    return DisputeResultsResponse(
        document_id=document.id,
        calculation_run_id=calculation_run_id,
        invoice_number=invoice_number,
        container_number=container_number,
        currency=currency,
        expected_charge=expected_charge,
        invoiced_charge=invoiced_charge,
        variance=variance,
        ledger_rows=[
            DayLedgerRowResponse(
                id=row.id,
                local_date=row.local_date,
                clock_day_ordinal=row.clock_day_ordinal,
                eligible_free_day=row.eligible_free_day,
                free_day_ordinal=row.free_day_ordinal,
                chargeable=row.chargeable,
                chargeable_day_ordinal=row.chargeable_day_ordinal,
                daily_rate=row.daily_rate,
                amount=row.amount,
                currency=row.currency,
                reason_code=row.reason_code,
                impediment_codes=list(row.impediment_codes or []),
                evidence_ids=list(row.evidence_ids or []),
            )
            for row in ledger_rows
        ],
        findings=[
            FindingResponse(
                id=finding.id,
                reason_code=finding.reason_code,
                posture=finding.posture,
                severity=finding.severity,
                affected_dates=list(finding.affected_dates or []),
                disputed_amount=finding.disputed_amount,
                disputed_currency=finding.disputed_currency,
                status=finding.status,
                rule_version_ids=list(finding.rule_version_ids or []),
                evidence_ids=list(finding.evidence_ids or []),
            )
            for finding in findings
        ],
    )
