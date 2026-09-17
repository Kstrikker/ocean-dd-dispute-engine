"""Pure deterministic D&D audit logic.

This module performs no network calls and imports no AI SDK. All dates, day
classification, rate application, monetary totals, and variances are computed
here using deterministic Python and Decimal arithmetic.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any


CONTAINER_PATTERN = re.compile(r"^[A-Z]{4}[0-9]{7}$")
ISO_6346_LETTER_VALUES = {
    "A": 10,
    "B": 12,
    "C": 13,
    "D": 14,
    "E": 15,
    "F": 16,
    "G": 17,
    "H": 18,
    "I": 19,
    "J": 20,
    "K": 21,
    "L": 23,
    "M": 24,
    "N": 25,
    "O": 26,
    "P": 27,
    "Q": 28,
    "R": 29,
    "S": 30,
    "T": 31,
    "U": 32,
    "V": 34,
    "W": 35,
    "X": 36,
    "Y": 37,
    "Z": 38,
}
ZERO = Decimal("0.0000")


def validate_iso6346(container_number: str) -> bool:
    """Validate an ISO 6346 container number and its check digit."""

    normalized = container_number.strip().upper()
    if not CONTAINER_PATTERN.fullmatch(normalized):
        return False

    total = 0
    for position, character in enumerate(normalized[:10]):
        if character.isdigit():
            value = int(character)
        else:
            value = ISO_6346_LETTER_VALUES[character]
        total += value * (2**position)

    expected_check_digit = (total % 11) % 10
    return expected_check_digit == int(normalized[-1])


def _parse_date(value: Any, field_name: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be an ISO-8601 date string.")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} is not a valid ISO-8601 date: {value}") from exc


def _decimal(value: Any, field_name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} is not a valid decimal value.") from exc
    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite.")
    return result


def _money(value: Any, field_name: str) -> tuple[Decimal, str]:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a money object.")
    amount = _decimal(value.get("amount"), f"{field_name}.amount")
    currency = value.get("currency")
    if not isinstance(currency, str) or len(currency) != 3:
        raise ValueError(f"{field_name}.currency must be a three-letter code.")
    return amount, currency.upper()


def _matching_rate_tiers(
    extracted_data: dict[str, Any], charge_type: str, currency: str
) -> list[dict[str, Any]]:
    tiers: list[dict[str, Any]] = []
    for rule in extracted_data.get("tariff_rules", []):
        for tier in rule.get("rate_tiers", []):
            if tier.get("charge_type") != charge_type:
                continue
            _, tier_currency = _money(tier.get("rate"), "rate_tier.rate")
            if tier_currency != currency:
                raise ValueError("Rate-tier and invoice currencies do not match.")
            tiers.append(tier)

    tiers.sort(key=lambda tier: int(tier["from_day"]))
    return tiers


def _invoice_rate_tiers(
    charge_line: dict[str, Any], charge_type: str, currency: str
) -> list[dict[str, Any]]:
    tiers: list[dict[str, Any]] = []
    for application in charge_line.get("rate_applications", []):
        if application.get("from_day") is None:
            continue
        _, application_currency = _money(
            application.get("rate"), "rate_application.rate"
        )
        if application_currency != currency:
            raise ValueError("Invoice-rate and line-total currencies do not match.")
        tiers.append(
            {
                "charge_type": charge_type,
                "from_day": application["from_day"],
                "to_day": application.get("to_day"),
                "rate": application["rate"],
            }
        )
    tiers.sort(key=lambda tier: int(tier["from_day"]))
    return tiers


def _select_rate(
    tiers: list[dict[str, Any]], chargeable_day_ordinal: int
) -> tuple[Decimal, str]:
    matches = [
        tier
        for tier in tiers
        if int(tier["from_day"]) <= chargeable_day_ordinal
        and (
            tier.get("to_day") is None
            or chargeable_day_ordinal <= int(tier["to_day"])
        )
    ]
    if len(matches) != 1:
        raise ValueError(
            f"Expected one rate tier for chargeable day {chargeable_day_ordinal}; "
            f"found {len(matches)}."
        )
    return _money(matches[0]["rate"], "selected_rate_tier.rate")


def _iter_charge_lines(extracted_data: dict[str, Any]):
    invoices = extracted_data.get("invoices")
    if not isinstance(invoices, list) or not invoices:
        raise ValueError("At least one extracted invoice is required for audit.")

    for invoice_index, invoice in enumerate(invoices):
        charge_lines = invoice.get("charge_lines")
        if not isinstance(charge_lines, list) or not charge_lines:
            raise ValueError(f"Invoice {invoice_index} has no charge lines.")
        for line_index, charge_line in enumerate(charge_lines):
            yield invoice_index, line_index, invoice, charge_line


def run_deterministic_audit(extracted_data: dict[str, Any]) -> dict[str, Any]:
    """Build deterministic day-ledger rows and variance findings."""

    if not isinstance(extracted_data, dict):
        raise TypeError("extracted_data must be a dictionary.")

    evidence_ids = [
        str(item["evidence_id"])
        for item in extracted_data.get("field_evidence", [])
        if isinstance(item, dict) and item.get("evidence_id")
    ]
    rule_version_ids = [
        str(rule["rule_id"])
        for rule in extracted_data.get("tariff_rules", [])
        if isinstance(rule, dict) and rule.get("rule_id")
    ]

    ledger_rows: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    line_summaries: list[dict[str, Any]] = []

    for invoice_index, line_index, invoice, charge_line in _iter_charge_lines(
        extracted_data
    ):
        pointer = f"/invoices/{invoice_index}/charge_lines/{line_index}"
        container_number = str(charge_line.get("container_number", "")).upper()
        charge_type = str(charge_line.get("charge_type", ""))

        if not validate_iso6346(container_number):
            findings.append(
                {
                    "reason_code": "INVALID_CONTAINER_CHECK_DIGIT",
                    "posture": "DETERMINISTIC",
                    "severity": "ERROR",
                    "affected_dates": [],
                    "disputed_amount": None,
                    "disputed_currency": None,
                    "status": "OPEN",
                    "rule_version_ids": rule_version_ids,
                    "evidence_ids": evidence_ids,
                    "container_number": container_number,
                    "source_pointer": pointer,
                }
            )
            continue

        free_time_days = charge_line.get("free_time_days")
        if not isinstance(free_time_days, int) or free_time_days < 0:
            raise ValueError(f"{pointer}/free_time_days must be a non-negative integer.")

        charge_start = _parse_date(
            charge_line.get("charge_start_date"),
            f"{pointer}/charge_start_date",
        )
        charge_end = _parse_date(
            charge_line.get("charge_end_date"),
            f"{pointer}/charge_end_date",
        )
        if charge_end < charge_start:
            raise ValueError(f"{pointer} has charge_end_date before charge_start_date.")

        invoiced_amount, invoice_currency = _money(
            charge_line.get("line_total"), f"{pointer}/line_total"
        )
        tiers = _matching_rate_tiers(
            extracted_data, charge_type, invoice_currency
        ) or _invoice_rate_tiers(charge_line, charge_type, invoice_currency)
        if not tiers:
            raise ValueError(f"{pointer} has no deterministic rate tiers.")

        expected_total = ZERO
        chargeable_day_ordinal = 0
        billable_dates: list[str] = []
        cursor = charge_start
        clock_day_ordinal = 0

        while cursor <= charge_end:
            clock_day_ordinal += 1
            eligible_free_day = clock_day_ordinal <= free_time_days
            free_day_ordinal = clock_day_ordinal if eligible_free_day else None
            chargeable = not eligible_free_day
            daily_rate = ZERO
            row_amount = ZERO
            current_chargeable_ordinal: int | None = None

            if chargeable:
                chargeable_day_ordinal += 1
                current_chargeable_ordinal = chargeable_day_ordinal
                daily_rate, rate_currency = _select_rate(
                    tiers, chargeable_day_ordinal
                )
                if rate_currency != invoice_currency:
                    raise ValueError("Selected rate and invoice currencies do not match.")
                row_amount = daily_rate
                expected_total += row_amount
                billable_dates.append(cursor.isoformat())

            ledger_rows.append(
                {
                    "container_number": container_number,
                    "charge_type": charge_type,
                    "local_date": cursor.isoformat(),
                    "clock_day_ordinal": clock_day_ordinal,
                    "eligible_free_day": eligible_free_day,
                    "free_day_ordinal": free_day_ordinal,
                    "impediment_codes": [],
                    "chargeable": chargeable,
                    "chargeable_day_ordinal": current_chargeable_ordinal,
                    "rate_tier_id": None,
                    "daily_rate": format(daily_rate, "f"),
                    "currency": invoice_currency,
                    "amount": format(row_amount, "f"),
                    "reason_code": "FREE_TIME" if eligible_free_day else "BILLABLE",
                    "evidence_ids": evidence_ids,
                    "source_pointer": pointer,
                }
            )
            cursor += timedelta(days=1)

        variance = invoiced_amount - expected_total
        invoiced_dates = {
            str(value) for value in charge_line.get("specific_charged_dates", [])
        }
        excess_dates = sorted(invoiced_dates.difference(billable_dates))

        line_summaries.append(
            {
                "invoice_number": invoice.get("invoice_number"),
                "container_number": container_number,
                "charge_type": charge_type,
                "free_time_days": free_time_days,
                "period_start": charge_start.isoformat(),
                "period_end": charge_end.isoformat(),
                "billable_days": chargeable_day_ordinal,
                "invoiced_amount": format(invoiced_amount, "f"),
                "expected_amount": format(expected_total, "f"),
                "variance_amount": format(variance, "f"),
                "currency": invoice_currency,
            }
        )

        if variance > ZERO:
            findings.append(
                {
                    "reason_code": "BILLED_AMOUNT_EXCEEDS_DETERMINISTIC_TOTAL",
                    "posture": "DETERMINISTIC",
                    "severity": "HIGH",
                    "affected_dates": excess_dates,
                    "disputed_amount": format(variance, "f"),
                    "disputed_currency": invoice_currency,
                    "status": "OPEN",
                    "rule_version_ids": rule_version_ids,
                    "evidence_ids": evidence_ids,
                    "container_number": container_number,
                    "source_pointer": pointer,
                }
            )

    return {
        "ledger_rows": ledger_rows,
        "findings": findings,
        "line_summaries": line_summaries,
    }

