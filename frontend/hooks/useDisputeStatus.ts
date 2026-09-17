"use client";

import { useQuery } from "@tanstack/react-query";

import {
  API_BASE_URL,
  TENANT_ID,
  apiError,
  type DisputeStatusResponse,
} from "@/lib/api";

const TERMINAL_STATUSES = new Set(["READY_FOR_APPROVAL", "FAILED"]);

export function useDisputeStatus(documentId: string | null) {
  return useQuery({
    queryKey: ["dispute-status", documentId],
    enabled: Boolean(documentId),
    queryFn: async ({ signal }) => {
      const response = await fetch(`${API_BASE_URL}/status/${documentId}`, {
        headers: { "X-Tenant-ID": TENANT_ID },
        signal,
      });

      if (!response.ok) {
        throw await apiError(response, "Unable to retrieve extraction status");
      }

      return (await response.json()) as DisputeStatusResponse;
    },
    refetchInterval: (query) => {
      const currentStatus = query.state.data?.status;
      return currentStatus && TERMINAL_STATUSES.has(currentStatus) ? false : 2_000;
    },
    refetchIntervalInBackground: true,
  });
}
