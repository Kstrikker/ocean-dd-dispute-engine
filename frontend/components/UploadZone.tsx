"use client";

import { useRef, useState, type DragEvent, type KeyboardEvent } from "react";
import { useMutation } from "@tanstack/react-query";
import { AlertCircle, CheckCircle2, FileText, LoaderCircle, UploadCloud } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { API_BASE_URL, TENANT_ID, apiError, type UploadResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

const MAX_FILE_BYTES = 25 * 1024 * 1024;

interface UploadZoneProps {
  onUploaded: (response: UploadResponse, file: File) => void;
}

function validatePdf(file: File) {
  if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
    throw new Error("Choose a PDF invoice. Other file types are not accepted.");
  }
  if (file.size === 0) {
    throw new Error("The selected PDF is empty.");
  }
  if (file.size > MAX_FILE_BYTES) {
    throw new Error("The PDF exceeds the 25 MB upload limit.");
  }
}

export function UploadZone({ onUploaded }: UploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [clientError, setClientError] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      validatePdf(file);
      const body = new FormData();
      body.append("file", file);

      const response = await fetch(`${API_BASE_URL}/upload/`, {
        method: "POST",
        headers: { "X-Tenant-ID": TENANT_ID },
        body,
      });
      if (!response.ok) {
        throw await apiError(response, "The invoice could not be uploaded");
      }
      return { data: (await response.json()) as UploadResponse, file };
    },
    onMutate: () => setClientError(null),
    onSuccess: ({ data, file }) => onUploaded(data, file),
  });

  const submitFile = (file?: File) => {
    if (!file || uploadMutation.isPending) return;
    try {
      validatePdf(file);
      uploadMutation.mutate(file);
    } catch (error) {
      setClientError(error instanceof Error ? error.message : "Invalid PDF.");
    }
  };

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragActive(false);
    submitFile(event.dataTransfer.files[0]);
  };

  const handleKeyboard = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      inputRef.current?.click();
    }
  };

  const error = clientError ?? uploadMutation.error?.message;

  return (
    <section id="upload" aria-labelledby="upload-heading" className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        aria-label="Upload a D&D invoice PDF"
        aria-busy={uploadMutation.isPending}
        onKeyDown={handleKeyboard}
        onClick={() => inputRef.current?.click()}
        onDragEnter={(event) => {
          event.preventDefault();
          setDragActive(true);
        }}
        onDragOver={(event) => event.preventDefault()}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragActive(false);
        }}
        onDrop={handleDrop}
        className={cn(
          "focus-ring group relative flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed bg-card px-6 py-10 text-center shadow-sm transition-all",
          dragActive
            ? "border-primary bg-primary/5 ring-4 ring-primary/10"
            : "border-slate-300 hover:border-primary/60 hover:bg-accent/40 dark:border-slate-700",
          uploadMutation.isPending && "cursor-wait opacity-80",
        )}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="sr-only"
          disabled={uploadMutation.isPending}
          onChange={(event) => {
            submitFile(event.target.files?.[0]);
            event.target.value = "";
          }}
        />
        <div className="mb-4 flex size-12 items-center justify-center rounded-xl border bg-background text-primary shadow-sm">
          {uploadMutation.isPending ? (
            <LoaderCircle aria-hidden="true" className="size-6 animate-spin" />
          ) : (
            <UploadCloud aria-hidden="true" className="size-6" />
          )}
        </div>
        <h2 id="upload-heading" className="text-base font-semibold">
          {uploadMutation.isPending ? "Uploading invoice…" : "Drop a D&D invoice here"}
        </h2>
        <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
          PDF only, up to 25 MB. The evidence compiler extracts source claims; deterministic Python calculates the result.
        </p>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="mt-5 pointer-events-none"
          tabIndex={-1}
          aria-hidden="true"
        >
          <FileText aria-hidden="true" />
          Select PDF
        </Button>
      </div>

      <div aria-live="polite">
        {error && (
          <Alert variant="destructive">
            <AlertCircle aria-hidden="true" />
            <AlertTitle>Upload failed</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        {uploadMutation.isSuccess && !error && (
          <div className="flex items-center gap-2 text-sm text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 aria-hidden="true" className="size-4" />
            Upload accepted. The extraction job is now being monitored.
          </div>
        )}
      </div>
    </section>
  );
}
