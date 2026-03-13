import { useQuery } from "@tanstack/react-query";
import type { UserProfile } from "@/types";
import { apiFetch } from "@/lib/api-client";

async function fetchMe(): Promise<UserProfile> {
  const res = await apiFetch("/api/me");
  if (!res.ok) throw new Error("Failed to fetch user");
  const raw = await res.json();
  return {
    id: raw.id,
    clerkId: raw.clerk_id,
    email: raw.email,
    name: raw.name,
    createdAt: raw.created_at,
    companyCount: raw.company_count ?? 0,
    trackedEventCount: raw.tracked_event_count ?? 0,
  };
}

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
  });
}
