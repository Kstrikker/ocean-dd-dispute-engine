"use client";

import { useQuery } from "@tanstack/react-query";

import {
  API_BASE_URL,
  TENANT_ID,
  apiError,
  type DisputeResultsResponse,
} from "@/lib/api";

export function useDisputeResults(
  documentId: string | null,
  extractionStatus: string | undefined,
) {
  const ready = extractionStatus === "READY_FOR_APPROVAL";

  return useQuery({
    queryKey: ["dispute-results", documentId],
    enabled: Boolean(documentId) && ready,
    queryFn: async ({ signal }) => {
      const response = await fetch(`${API_BASE_URL}/results/${documentId}`, {
        headers: { "X-Tenant-ID": TENANT_ID },
        signal,
      });

      if (!response.ok) {
        throw await apiError(response, "Unable to retrieve audit results");
      }

      return (await response.json()) as DisputeResultsResponse;
    },
    staleTime: Number.POSITIVE_INFINITY,
    retry: 2,
    refetchOnWindowFocus: false,
  });
}
