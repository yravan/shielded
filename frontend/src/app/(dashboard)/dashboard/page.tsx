"use client";

import { Card, CardContent } from "@/components/ui/card";
import { PageHeader } from "@/components/shared/page-header";
import { EventCard } from "@/components/events/event-card";
import { EventCardSkeleton } from "@/components/events/event-card-skeleton";
import { useEvents } from "@/hooks/use-events";
import { Activity, AlertTriangle, Building2, TrendingDown } from "lucide-react";

export default function DashboardPage() {
  const { data: events, isLoading } = useEvents();

  const totalEvents = events?.length ?? 0;
  const highProbEvents = events?.filter((e) => e.currentProbability > 0.5).length ?? 0;

  const stats = [
    { label: "Active Events", value: totalEvents, icon: Activity },
    { label: ">50% Probability", value: highProbEvents, icon: AlertTriangle },
    { label: "Companies Tracked", value: 5, icon: Building2 },
    { label: "Avg PM Savings", value: "28%", icon: TrendingDown },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="Overview of geopolitical risk exposure and hedging opportunities"
      />

      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="flex items-center gap-4 pt-6">
              <div className="rounded-md bg-primary/10 p-2">
                <stat.icon className="h-4 w-4 text-primary" />
              </div>
              <div>
                <p className="text-3xl font-semibold font-mono">{stat.value}</p>
                <p className="text-[11px] text-muted-foreground">{stat.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div>
        <h2 className="text-lg font-semibold mb-4">Active Events</h2>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading
            ? Array.from({ length: 6 }).map((_, i) => <EventCardSkeleton key={i} />)
            : events?.map((event) => <EventCard key={event.id} event={event} />)}
        </div>
      </div>
    </div>
  );
}
