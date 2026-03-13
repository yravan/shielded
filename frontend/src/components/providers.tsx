"use client";

import { useState, useEffect, useRef } from "react";
import { ThemeProvider } from "next-themes";
import { QueryClient, QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import { TooltipProvider } from "@/components/ui/tooltip";

function AuthCacheCleaner() {
  const { userId } = useAuth();
  const queryClient = useQueryClient();
  const prevUserId = useRef(userId);

  useEffect(() => {
    if (prevUserId.current && prevUserId.current !== userId) {
      queryClient.removeQueries();
    }
    prevUserId.current = userId;
  }, [userId, queryClient]);

  return null;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000,
            gcTime: 10 * 60 * 1000,
          },
        },
      })
  );

  return (
    <ThemeProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
    >
      <QueryClientProvider client={queryClient}>
        <AuthCacheCleaner />
        <TooltipProvider>{children}</TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
}
