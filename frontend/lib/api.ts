export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export const TENANT_ID = process.env.NEXT_PUBLIC_TENANT_ID ?? "local-dev";

export interface UploadResponse {
  case_id: string;
  document_id: string;
  status: string;
  message: string;
}

export interface DisputeStatusResponse {
  case_id: string;
  document_id: string;
  extraction_run_id: string;
  status: string;
  updated_at: string;
}

export type MoneyValue = string | number;

export interface DayLedgerRow {
  id: string;
  local_date: string;
  clock_day_ordinal: number;
  eligible_free_day: boolean;
  free_day_ordinal: number | null;
  chargeable: boolean;
  chargeable_day_ordinal: number | null;
  daily_rate: MoneyValue | null;
  amount: MoneyValue;
  currency: string;
  reason_code: string;
  impediment_codes: string[];
  evidence_ids: string[];
}

export interface Finding {
  id: string;
  reason_code: string;
  posture: string;
  severity: string;
  affected_dates: string[];
  disputed_amount: MoneyValue | null;
  disputed_currency: string | null;
  status: string;
  rule_version_ids: string[];
  evidence_ids: string[];
}

export interface DisputeResultsResponse {
  document_id: string;
  calculation_run_id: string;
  invoice_number: string;
  container_number: string;
  currency: string;
  expected_charge: MoneyValue;
  invoiced_charge: MoneyValue;
  variance: MoneyValue;
  ledger_rows: DayLedgerRow[];
  findings: Finding[];
}

interface ApiErrorBody {
  detail?: string | { message?: string };
}

export async function apiError(response: Response, fallback: string) {
  let message = fallback;

  try {
    const body = (await response.json()) as ApiErrorBody;
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (body.detail?.message) {
      message = body.detail.message;
    }
  } catch {
    // Keep the safe fallback when the backend did not return JSON.
  }

  return new Error(`${message} (${response.status})`);
}
