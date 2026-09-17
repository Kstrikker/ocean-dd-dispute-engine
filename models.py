"""Core SQLAlchemy models for the Ocean Freight D&D Dispute Engine."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Tenant(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    retention_policy: Mapped[str | None] = mapped_column(Text, nullable=True)

    documents: Mapped[list[Document]] = relationship(back_populates="tenant")


class Document(TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_tenant_case", "tenant_id", "case_id"),
        Index("ix_documents_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    display_filename: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    tenant: Mapped[Tenant] = relationship(back_populates="documents")
    invoices: Mapped[list[Invoice]] = relationship(back_populates="document")


class ExtractionRun(TimestampMixin, Base):
    __tablename__ = "extraction_runs"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "input_fingerprint",
            name="uq_extraction_runs_tenant_fingerprint",
        ),
        CheckConstraint(
            "jsonb_typeof(raw_model_response) = 'object'",
            name="raw_model_response_is_object",
        ),
        CheckConstraint(
            "jsonb_typeof(validated_payload) = 'object'",
            name="validated_payload_is_object",
        ),
        CheckConstraint(
            "jsonb_typeof(evidence_items) = 'array'",
            name="evidence_items_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(warnings) = 'array'",
            name="warnings_is_array",
        ),
        Index("ix_extraction_runs_tenant_case", "tenant_id", "case_id"),
        Index("ix_extraction_runs_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(100), nullable=False)
    parser_version: Mapped[str] = mapped_column(String(100), nullable=False)
    ocr_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    supersedes_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("extraction_runs.id", ondelete="RESTRICT"),
        nullable=True,
    )
    raw_model_response: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
    validated_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False
    )
    evidence_items: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    layout_snapshot: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    supersedes: Mapped[ExtractionRun | None] = relationship(
        remote_side="ExtractionRun.id",
        foreign_keys=[supersedes_id],
    )


class Container(TimestampMixin, Base):
    __tablename__ = "containers"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "container_number",
            name="uq_containers_tenant_number",
        ),
        CheckConstraint(
            "container_number ~ '^[A-Z]{4}[0-9]{7}$'",
            name="container_number_iso6346_format",
        ),
        CheckConstraint(
            "iso6346_check_digit_valid IS TRUE",
            name="container_check_digit_must_be_valid",
        ),
        CheckConstraint(
            "length_ft IS NULL OR length_ft IN (20, 40, 45, 48, 53)",
            name="container_supported_length",
        ),
        Index("ix_containers_tenant_number", "tenant_id", "container_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    container_number: Mapped[str] = mapped_column(String(11), nullable=False)
    iso6346_check_digit_valid: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    iso_size_type_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    length_ft: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height_class: Mapped[str | None] = mapped_column(String(50), nullable=True)
    equipment_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ownership: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hazardous: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    charge_lines: Mapped[list[InvoiceChargeLine]] = relationship(
        back_populates="container"
    )
    ledger_rows: Mapped[list[DayLedgerRow]] = relationship(
        back_populates="container"
    )


class Invoice(TimestampMixin, Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "invoice_number",
            name="uq_invoices_tenant_number",
        ),
        CheckConstraint(
            "subtotal_currency IS NULL OR char_length(subtotal_currency) = 3",
            name="subtotal_currency_iso_length",
        ),
        CheckConstraint(
            "tax_currency IS NULL OR char_length(tax_currency) = 3",
            name="tax_currency_iso_length",
        ),
        CheckConstraint(
            "credit_currency IS NULL OR char_length(credit_currency) = 3",
            name="credit_currency_iso_length",
        ),
        CheckConstraint(
            "char_length(total_currency) = 3",
            name="total_currency_iso_length",
        ),
        Index("ix_invoices_tenant_issue_date", "tenant_id", "issue_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="RESTRICT"),
        nullable=False,
    )
    document_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    invoice_number: Mapped[str] = mapped_column(String(255), nullable=False)
    invoice_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    supersedes_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="RESTRICT"),
        nullable=True,
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    underlying_invoice_number: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    underlying_invoice_issue_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    billing_party_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    billed_party_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    liability_basis: Mapped[str | None] = mapped_column(Text, nullable=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    subtotal_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    subtotal_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    tax_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    credit_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    credit_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    total_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    document: Mapped[Document] = relationship(back_populates="invoices")
    supersedes: Mapped[Invoice | None] = relationship(
        remote_side="Invoice.id",
        foreign_keys=[supersedes_invoice_id],
    )
    charge_lines: Mapped[list[InvoiceChargeLine]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class InvoiceChargeLine(TimestampMixin, Base):
    __tablename__ = "invoice_charge_lines"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "invoice_id",
            "line_id",
            name="uq_invoice_charge_lines_tenant_invoice_line",
        ),
        UniqueConstraint(
            "tenant_id",
            "invoice_id",
            "container_id",
            "charge_type",
            name="uq_invoice_charge_lines_invoice_container_charge",
        ),
        CheckConstraint("billed_days >= 0", name="billed_days_nonnegative"),
        CheckConstraint(
            "subtotal_currency IS NULL OR char_length(subtotal_currency) = 3",
            name="charge_subtotal_currency_iso_length",
        ),
        CheckConstraint(
            "tax_currency IS NULL OR char_length(tax_currency) = 3",
            name="charge_tax_currency_iso_length",
        ),
        CheckConstraint(
            "administrative_fee_currency IS NULL "
            "OR char_length(administrative_fee_currency) = 3",
            name="charge_admin_currency_iso_length",
        ),
        CheckConstraint(
            "char_length(line_total_currency) = 3",
            name="charge_total_currency_iso_length",
        ),
        Index(
            "ix_invoice_charge_lines_tenant_container",
            "tenant_id",
            "container_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    container_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("containers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    line_id: Mapped[str] = mapped_column(String(128), nullable=False)
    charge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    free_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    free_time_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    free_time_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    container_availability_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    earliest_return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    charge_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    charge_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    billed_days: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    rate_source_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rate_source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rate_source_number: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    rate_source_section: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    subtotal_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    subtotal_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True)
    tax_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)
    administrative_fee_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    administrative_fee_currency: Mapped[str | None] = mapped_column(
        String(3), nullable=True
    )
    line_total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False
    )
    line_total_currency: Mapped[str] = mapped_column(String(3), nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="charge_lines")
    container: Mapped[Container] = relationship(back_populates="charge_lines")


class DayLedgerRow(TimestampMixin, Base):
    __tablename__ = "day_ledger_rows"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "calculation_run_id",
            "container_id",
            "charge_type",
            "local_date",
            name="uq_day_ledger_run_container_charge_date",
        ),
        CheckConstraint(
            "clock_day_ordinal >= 1",
            name="clock_day_ordinal_positive",
        ),
        CheckConstraint(
            "free_day_ordinal IS NULL OR free_day_ordinal >= 1",
            name="free_day_ordinal_positive",
        ),
        CheckConstraint(
            "chargeable_day_ordinal IS NULL OR chargeable_day_ordinal >= 1",
            name="chargeable_day_ordinal_positive",
        ),
        CheckConstraint(
            "jsonb_typeof(impediment_codes) = 'array'",
            name="impediment_codes_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(evidence_ids) = 'array'",
            name="ledger_evidence_ids_is_array",
        ),
        CheckConstraint(
            "char_length(currency) = 3",
            name="ledger_currency_iso_length",
        ),
        Index(
            "ix_day_ledger_tenant_calculation",
            "tenant_id",
            "calculation_run_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    calculation_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    container_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("containers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    charge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    clock_day_ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    eligible_free_day: Mapped[bool] = mapped_column(Boolean, nullable=False)
    free_day_ordinal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    impediment_codes: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    chargeable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    chargeable_day_ordinal: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    rate_tier_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    daily_rate: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    evidence_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )

    container: Mapped[Container] = relationship(back_populates="ledger_rows")


class Finding(TimestampMixin, Base):
    __tablename__ = "findings"
    __table_args__ = (
        CheckConstraint(
            "jsonb_typeof(affected_dates) = 'array'",
            name="affected_dates_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(rule_version_ids) = 'array'",
            name="finding_rule_version_ids_is_array",
        ),
        CheckConstraint(
            "jsonb_typeof(evidence_ids) = 'array'",
            name="finding_evidence_ids_is_array",
        ),
        CheckConstraint(
            "disputed_currency IS NULL OR char_length(disputed_currency) = 3",
            name="finding_currency_iso_length",
        ),
        Index("ix_findings_tenant_status", "tenant_id", "status"),
        Index(
            "ix_findings_tenant_evaluation",
            "tenant_id",
            "compliance_evaluation_id",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("tenants.tenant_id", ondelete="RESTRICT"),
        nullable=False,
    )
    compliance_evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    calculation_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    posture: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    affected_dates: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    disputed_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(18, 4), nullable=True
    )
    disputed_currency: Mapped[str | None] = mapped_column(
        String(3), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    rule_version_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )
    evidence_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
    )


__all__ = [
    "Base",
    "Container",
    "DayLedgerRow",
    "Document",
    "ExtractionRun",
    "Finding",
    "Invoice",
    "InvoiceChargeLine",
    "Tenant",
]
