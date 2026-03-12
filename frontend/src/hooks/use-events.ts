import { useQuery } from "@tanstack/react-query";
import { mockEvents, getEventById } from "@/lib/mock-data";
import type { GeopoliticalEvent } from "@/types";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchEvents(): Promise<GeopoliticalEvent[]> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 300));
    return mockEvents;
  }
  const res = await fetch(`${API_URL}/api/events`);
  if (!res.ok) throw new Error("Failed to fetch events");
  const data = await res.json();
  return data.items;
}

async function fetchEvent(id: string): Promise<GeopoliticalEvent | undefined> {
  if (USE_MOCKS) {
    await new Promise((r) => setTimeout(r, 200));
    return getEventById(id);
  }
  const res = await fetch(`${API_URL}/api/events/${id}`);
  if (!res.ok) throw new Error("Failed to fetch event");
  return res.json();
}

export function useEvents() {
  return useQuery({ queryKey: ["events"], queryFn: fetchEvents });
}

export function useEvent(id: string) {
  return useQuery({
    queryKey: ["events", id],
    queryFn: () => fetchEvent(id),
    enabled: !!id,
  });
}
