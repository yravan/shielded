"use client";

import { useState } from "react";
import Link from "next/link";

import { EventCard } from "@/components/events/event-card";
import { EventCardSkeleton } from "@/components/events/event-card-skeleton";
import { EventSuggestions } from "@/components/events/event-suggestions";
import { Button } from "@/components/ui/button";
import { useEvents } from "@/hooks/use-events";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Compass, Globe } from "lucide-react";
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
      <div className="flex items-center justify-between mb-2">
        <div />
        <Link href="/explore">
          <Button variant="outline" size="sm">
            <Compass className="h-4 w-4 mr-1.5" />
            Explore More Events
          </Button>
        </Link>
      </div>

      <EventSuggestions />

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
        <div className="text-center py-16 space-y-4">
          <Globe className="h-12 w-12 mx-auto text-muted-foreground/50" />
          <div>
            <p className="text-muted-foreground">You haven&apos;t tracked any events yet.</p>
            <Link
              href="/explore"
              className="text-primary hover:underline text-sm font-medium"
            >
              Browse events &rarr;
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
