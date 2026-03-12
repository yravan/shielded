"use client";

import { useState } from "react";
import { PageHeader } from "@/components/shared/page-header";
import { EventCard } from "@/components/events/event-card";
import { EventCardSkeleton } from "@/components/events/event-card-skeleton";
import { useEvents } from "@/hooks/use-events";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { EventCategory } from "@/types";

const categories: Array<{ value: EventCategory | "all"; label: string }> = [
  { value: "all", label: "All Categories" },
  { value: "geopolitical", label: "Geopolitical" },
  { value: "trade", label: "Trade" },
  { value: "regulatory", label: "Regulatory" },
  { value: "climate", label: "Climate" },
  { value: "conflict", label: "Conflict" },
  { value: "economic", label: "Economic" },
];

export default function EventsPage() {
  const { data: events, isLoading } = useEvents();
  const [category, setCategory] = useState("all");
  const [region, setRegion] = useState("all");

  const handleCategoryChange = (v: string | null) => setCategory(v ?? "all");
  const handleRegionChange = (v: string | null) => setRegion(v ?? "all");

  const regions = ["all", ...new Set(events?.map((e) => e.region) ?? [])];

  const filtered = events?.filter((e) => {
    if (category !== "all" && e.category !== category) return false;
    if (region !== "all" && e.region !== region) return false;
    return true;
  });

  return (
    <div className="space-y-8">
      <PageHeader
        title="Events"
        description="Monitor geopolitical events with real-time probability data"
      />

      <div className="flex gap-3">
        <Select value={category} onValueChange={handleCategoryChange}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent>
            {categories.map((c) => (
              <SelectItem key={c.value} value={c.value}>
                {c.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={region} onValueChange={handleRegionChange}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Region" />
          </SelectTrigger>
          <SelectContent>
            {regions.map((r) => (
              <SelectItem key={r} value={r}>
                {r === "all" ? "All Regions" : r}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <EventCardSkeleton key={i} />)
          : filtered?.map((event) => <EventCard key={event.id} event={event} />)}
      </div>

      {filtered?.length === 0 && !isLoading && (
        <p className="text-center text-muted-foreground py-12">
          No events match your filters.
        </p>
      )}
    </div>
  );
}
