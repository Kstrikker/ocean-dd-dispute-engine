"use client";

import { AlertTriangle, Calculator, CheckCircle2, FileText, Scale } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { DisputeResultsResponse, Finding, MoneyValue } from "@/lib/api";
import { cn, formatCurrency, formatDate } from "@/lib/utils";

interface ResultsDashboardProps {
  result?: DisputeResultsResponse;
  isLoading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

const FINDING_TITLES: Record<string, string> = {
  BILLED_AMOUNT_EXCEEDS_DETERMINISTIC_TOTAL: "Invoice exceeds deterministic total",
  WRONG_FREE_TIME_APPLIED: "DISPUTE: Wrong Free Time Applied",
  INVALID_CONTAINER_CHECK_DIGIT: "Invalid container check digit",
};

const REASON_LABELS: Record<string, string> = {
  FREE_TIME: "Contractual free time",
  BILLABLE: "Billable under selected tariff tier",
};

function toAmount(value: MoneyValue | null | undefined): number {
  if (value === null || value === undefined) return 0;
  const amount = typeof value === "number" ? value : Number(value);
  return Number.isFinite(amount) ? amount : 0;
}

function humanizeCode(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function findingDescription(finding: Finding, currency: string): string {
  const amount = toAmount(finding.disputed_amount);
  const amountText = amount > 0
    ? `${formatCurrency(amount, finding.disputed_currency ?? currency)} is currently disputed.`
    : "This finding requires review before the case can be approved.";
  const dateText = finding.affected_dates.length > 0
    ? ` Affected dates: ${finding.affected_dates.map(formatDate).join(", ")}.`
    : "";
  return `${amountText}${dateText}`;
}

function findingSource(finding: Finding): string {
  if (finding.rule_version_ids.length > 0) {
    return `Rule ${finding.rule_version_ids.join(", ")}`;
  }
  if (finding.evidence_ids.length > 0) {
    return `Evidence ${finding.evidence_ids.join(", ")}`;
  }
  return `${finding.posture} evaluation`;
}

function ResultsSkeleton() {
  return (
    <div aria-label="Loading dispute results" aria-busy="true" className="space-y-6">
      <span className="sr-only">Loading dispute results</span>
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <Card key={item}>
            <CardContent className="space-y-3 p-5">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-9 w-36" />
              <Skeleton className="h-3 w-44" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardContent className="space-y-3 p-5">
          <Skeleton className="h-5 w-44" />
          {[0, 1, 2, 3, 4].map((item) => (
            <Skeleton key={item} className="h-11 w-full" />
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

function KpiCard({
  label,
  value,
  description,
  variant = "default",
  icon: Icon,
}: {
  label: string;
  value: string;
  description: string;
  variant?: "default" | "danger" | "success";
  icon: typeof Calculator;
}) {
  return (
    <Card
      className={cn(
        variant === "danger" && "border-red-300 bg-red-50/70 dark:border-red-900 dark:bg-red-950/25",
        variant === "success" && "border-emerald-300 bg-emerald-50/70 dark:border-emerald-900 dark:bg-emerald-950/25",
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
            <p className={cn("mt-2 text-3xl font-semibold tracking-tight tabular-nums", variant === "danger" && "text-red-700 dark:text-red-300", variant === "success" && "text-emerald-700 dark:text-emerald-300")}>
              {value}
            </p>
          </div>
          <span className="flex size-9 items-center justify-center rounded-lg border bg-background/80 text-muted-foreground">
            <Icon aria-hidden="true" className="size-[18px]" />
          </span>
        </div>
        <p className="mt-3 text-xs leading-5 text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

export function ResultsDashboard({ result, isLoading = false, error = null, onRetry }: ResultsDashboardProps) {
  if (isLoading) return <ResultsSkeleton />;

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle aria-hidden="true" />
        <AlertTitle>Results unavailable</AlertTitle>
        <AlertDescription>
          <p>{error}</p>
          {onRetry && (
            <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
              Retry results
            </Button>
          )}
        </AlertDescription>
      </Alert>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardContent className="flex min-h-48 flex-col items-center justify-center text-center">
          <FileText aria-hidden="true" className="mb-3 size-8 text-muted-foreground" />
          <p className="font-medium">No completed audit selected</p>
          <p className="mt-1 text-sm text-muted-foreground">Upload an invoice to generate a deterministic ledger.</p>
        </CardContent>
      </Card>
    );
  }

  const expectedCharge = toAmount(result.expected_charge);
  const invoicedCharge = toAmount(result.invoiced_charge);
  const variance = toAmount(result.variance);
  const overcharged = variance > 0;
  const exact = variance === 0;

  return (
    <section id="results" aria-labelledby="results-heading" className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge variant="success"><CheckCircle2 aria-hidden="true" className="size-3" />Audit complete</Badge>
            <Badge variant="outline">{result.container_number}</Badge>
          </div>
          <h2 id="results-heading" className="text-xl font-semibold tracking-tight">Deterministic audit results</h2>
          <p className="mt-1 text-sm text-muted-foreground">Invoice {result.invoice_number} · evidence-compiled, Python-calculated</p>
        </div>
        <p className="text-xs text-muted-foreground">All amounts shown in {result.currency}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <KpiCard label="Expected Charge" value={formatCurrency(expectedCharge, result.currency)} description="Calculated from the selected rule and daily ledger." icon={Calculator} />
        <KpiCard label="Invoiced Charge" value={formatCurrency(invoicedCharge, result.currency)} description="Amount stated on the carrier invoice." icon={FileText} />
        <KpiCard
          label="Variance"
          value={formatCurrency(variance, result.currency)}
          description={exact ? "Invoice matches the deterministic ledger." : "Potential recoverable overcharge requiring approval."}
          icon={Scale}
          variant={overcharged ? "danger" : "success"}
        />
      </div>

      <Card>
        <CardHeader className="border-b">
          <CardTitle>Daily charge ledger</CardTitle>
          <CardDescription>Every date is classified before a rate is applied. No LLM arithmetic is used.</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[680px] border-collapse text-left text-sm">
              <caption className="sr-only">Deterministic daily ledger for container {result.container_number}</caption>
              <thead className="bg-muted/60 text-xs uppercase tracking-wide text-muted-foreground">
                <tr>
                  <th scope="col" className="px-5 py-3 font-medium">Date</th>
                  <th scope="col" className="px-5 py-3 font-medium">Status</th>
                  <th scope="col" className="px-5 py-3 text-right font-medium">Rate</th>
                  <th scope="col" className="px-5 py-3 font-medium">Reason</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {result.ledger_rows.map((row) => (
                  <tr key={row.id} className="transition-colors hover:bg-muted/35">
                    <td className="whitespace-nowrap px-5 py-3.5 font-medium tabular-nums">{formatDate(row.local_date)}</td>
                    <td className="px-5 py-3.5">
                      <Badge variant={row.chargeable ? "danger" : "success"}>
                        {row.chargeable ? "Chargeable" : "Free day"}
                      </Badge>
                    </td>
                    <td className="px-5 py-3.5 text-right font-medium tabular-nums">{formatCurrency(toAmount(row.daily_rate), row.currency)}</td>
                    <td className="px-5 py-3.5 text-muted-foreground">{REASON_LABELS[row.reason_code] ?? humanizeCode(row.reason_code)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <section id="findings" aria-labelledby="findings-heading" className="space-y-3">
        <div>
          <h2 id="findings-heading" className="text-lg font-semibold">Dispute findings</h2>
          <p className="mt-1 text-sm text-muted-foreground">Compliance and variance signals remain subject to human approval.</p>
        </div>
        {result.findings.length === 0 ? (
          <Alert>
            <CheckCircle2 aria-hidden="true" />
            <AlertTitle>No dispute findings</AlertTitle>
            <AlertDescription>The invoice matches the deterministic rules currently selected for this case.</AlertDescription>
          </Alert>
        ) : (
          result.findings.map((finding) => (
            <Alert key={finding.id} variant={finding.severity.toUpperCase() === "HIGH" || finding.severity.toUpperCase() === "ERROR" ? "destructive" : "warning"}>
              <AlertTriangle aria-hidden="true" />
              <AlertTitle>{FINDING_TITLES[finding.reason_code] ?? humanizeCode(finding.reason_code)}</AlertTitle>
              <AlertDescription>
                <p>{findingDescription(finding, result.currency)}</p>
                <p className="mt-2 text-xs font-medium opacity-75">Source: {findingSource(finding)}</p>
              </AlertDescription>
            </Alert>
          ))
        )}
      </section>
    </section>
  );
}
