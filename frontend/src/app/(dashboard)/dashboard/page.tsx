"use client";

import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import { EventCard } from "@/components/events/event-card";
import { EventCardSkeleton } from "@/components/events/event-card-skeleton";
import { RiskScoreBadge } from "@/components/risk/risk-score-badge";
import { useEvents } from "@/hooks/use-events";
import { useMe } from "@/hooks/use-me";
import { usePortfolioRisk } from "@/hooks/use-risk";
import { Activity, AlertTriangle, Building2, Compass, Shield } from "lucide-react";

export default function DashboardPage() {
  const { data: events, isLoading } = useEvents();
  const { data: me } = useMe();
  const { data: portfolioRisk } = usePortfolioRisk();

  const totalEvents = events?.length ?? 0;
  const highProbEvents = events?.filter((e) => e.currentProbability > 0.5).length ?? 0;

  const stats = [
    { label: "Tracked Events", value: totalEvents, icon: Activity },
    { label: ">50% Probability", value: highProbEvents, icon: AlertTriangle },
    { label: "Companies", value: me?.companyCount ?? 0, icon: Building2 },
  ];

  return (
    <div className="space-y-8">
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
        <Card>
          <CardContent className="flex items-center gap-4 pt-6">
            <div className="rounded-md bg-primary/10 p-2">
              <Shield className="h-4 w-4 text-primary" />
            </div>
            <div>
              {portfolioRisk && portfolioRisk.avgRiskScore > 0 ? (
                <>
                  <RiskScoreBadge score={Math.round(portfolioRisk.avgRiskScore)} size="md" />
                  <p className="text-[11px] text-muted-foreground mt-0.5">Portfolio Risk</p>
                </>
              ) : (
                <>
                  <p className="text-3xl font-semibold font-mono">--</p>
                  <p className="text-[11px] text-muted-foreground">Portfolio Risk</p>
                </>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Tracked Events</h2>
          <Link href="/explore">
            <Button variant="outline" size="sm">
              <Compass className="h-4 w-4 mr-1.5" />
              Explore Events
            </Button>
          </Link>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {isLoading
            ? Array.from({ length: 6 }).map((_, i) => <EventCardSkeleton key={i} />)
            : events?.length === 0
              ? (
                <div className="col-span-full text-center py-12">
                  <p className="text-muted-foreground">No tracked events yet.</p>
                  <Link href="/explore" className="text-primary hover:underline text-sm">
                    Browse events to start tracking &rarr;
                  </Link>
                </div>
              )
              : events?.map((event) => <EventCard key={event.id} event={event} />)}
        </div>
      </div>
    </div>
  );
}
