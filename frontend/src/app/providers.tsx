import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type * as React from "react";
import { Toaster } from "sonner";

import { ApiRequestError } from "../api";
import { AuthProvider } from "./auth";
import { AppErrorBoundary } from "./error-boundary";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (error instanceof ApiRequestError && error.status === 401) {
          return false;
        }
        return failureCount < 1;
      },
    },
  },
});

export function AppProviders({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AppErrorBoundary>
        <AuthProvider>{children}</AuthProvider>
      </AppErrorBoundary>
      <Toaster richColors position="top-right" />
    </QueryClientProvider>
  );
}
