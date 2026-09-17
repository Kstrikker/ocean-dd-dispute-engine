"use client";

import { useState } from "react";
import { AlertCircle, Clock3, FileCheck2, LoaderCircle, RotateCcw } from "lucide-react";

import { ResultsDashboard } from "@/components/ResultsDashboard";
import { UploadZone } from "@/components/UploadZone";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useDisputeResults } from "@/hooks/useDisputeResults";
import { useDisputeStatus } from "@/hooks/useDisputeStatus";
import type { UploadResponse } from "@/lib/api";

const STATUS_LABELS: Record<string, string> = {
  PENDING: "Queued",
  EXTRACTING: "Compiling evidence",
  READY_FOR_APPROVAL: "Ready for approval",
  FAILED: "Processing failed",
  ENQUEUE_FAILED: "Queue unavailable",
};

export default function DashboardPage() {
  const [upload, setUpload] = useState<UploadResponse | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const statusQuery = useDisputeStatus(upload?.document_id ?? null);
  const processingStatus = statusQuery.data?.status ?? upload?.status;
  const ready = processingStatus === "READY_FOR_APPROVAL";
  const failed = processingStatus === "FAILED" || processingStatus === "ENQUEUE_FAILED";
  const resultsQuery = useDisputeResults(upload?.document_id ?? null, processingStatus);

  const handleUploaded = (response: UploadResponse, file: File) => {
    setUpload(response);
    setFileName(file.name);
  };

  const reset = () => {
    setUpload(null);
    setFileName(null);
  };

  return (
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute inset-x-0 top-0 h-80 bg-[radial-gradient(circle_at_70%_0%,rgba(14,165,233,0.12),transparent_38%),radial-gradient(circle_at_20%_0%,rgba(37,99,235,0.1),transparent_32%)]" />
      <div className="relative mx-auto max-w-[1500px] space-y-8 px-4 py-10 sm:px-6 lg:px-8 lg:py-14">
        <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <div className="mb-3 flex items-center gap-2">
              <Badge variant="outline">Operations workspace</Badge>
              <span className="text-xs text-muted-foreground">US imports · Deterministic audit</span>
            </div>
            <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">D&amp;D dispute review</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
              Compile invoice evidence, replay the tariff clock, and prepare an auditable finding for human approval.
            </p>
          </div>
          {upload && (
            <Button variant="outline" onClick={reset}>
              <RotateCcw aria-hidden="true" /> Start another review
            </Button>
          )}
        </header>

        {!upload ? (
          <div className="grid gap-6 xl:grid-cols-[minmax(0,1.45fr)_minmax(300px,0.55fr)]">
            <UploadZone onUploaded={handleUploaded} />
            <Card>
              <CardHeader>
                <CardTitle>Controlled processing</CardTitle>
                <CardDescription>Each boundary is explicit and auditable.</CardDescription>
              </CardHeader>
              <CardContent>
                <ol className="space-y-5">
                  {[
                    ["01", "Upload", "FastAPI registers the PDF and creates a case."],
                    ["02", "Extract", "Gemini compiles schema-bound facts with evidence."],
                    ["03", "Calculate", "Python generates every free and chargeable day."],
                    ["04", "Approve", "A reviewer validates the finding before action."],
                  ].map(([step, title, description]) => (
                    <li key={step} className="flex gap-3">
                      <span className="flex size-8 shrink-0 items-center justify-center rounded-full border bg-muted text-xs font-semibold text-muted-foreground">{step}</span>
                      <div>
                        <p className="text-sm font-medium">{title}</p>
                        <p className="mt-0.5 text-xs leading-5 text-muted-foreground">{description}</p>
                      </div>
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          </div>
        ) : (
          <Card aria-live="polite">
            <CardContent className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex min-w-0 items-center gap-3">
                <span className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  {ready ? <FileCheck2 aria-hidden="true" /> : failed ? <AlertCircle aria-hidden="true" /> : <LoaderCircle aria-hidden="true" className="animate-spin" />}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{fileName}</p>
                  <p className="truncate text-xs text-muted-foreground">Document {upload.document_id}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Clock3 aria-hidden="true" className="size-4 text-muted-foreground" />
                <span className="text-sm font-medium">{STATUS_LABELS[processingStatus ?? ""] ?? processingStatus ?? "Checking status"}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {statusQuery.isError && upload && (
          <Alert variant="destructive">
            <AlertCircle aria-hidden="true" />
            <AlertTitle>Status check failed</AlertTitle>
            <AlertDescription>
              <p>{statusQuery.error.message}</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={() => statusQuery.refetch()}>Retry status check</Button>
            </AlertDescription>
          </Alert>
        )}

        {failed && (
          <Alert variant="destructive">
            <AlertCircle aria-hidden="true" />
            <AlertTitle>Document processing failed</AlertTitle>
            <AlertDescription>The source record is preserved. Start a new review after checking the API and worker logs.</AlertDescription>
          </Alert>
        )}

        {upload && !failed && (
          <ResultsDashboard
            isLoading={!ready || resultsQuery.isPending}
            result={resultsQuery.data}
            error={resultsQuery.error?.message ?? null}
            onRetry={() => resultsQuery.refetch()}
          />
        )}
      </div>
    </div>
  );
}
