"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { EventCardHeader } from "./event-card-header";
import { EventImpacts } from "./event-impacts";
import { ImpliedFinancials } from "./implied-financials";
import { MiniSparkline } from "@/components/charts/mini-sparkline";
import { useEventHistory } from "@/hooks/use-events";
import type { GeopoliticalEvent } from "@/types";

interface EventCardProps {
  event: GeopoliticalEvent;
}

export function EventCard({ event }: EventCardProps) {
  const { data: history, isLoading: historyLoading } = useEventHistory(event.id);

  return (
    <Link href={`/events/${event.id}`}>
      <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
        <CardHeader className="pb-3">
          <EventCardHeader
            title={event.title}
            category={event.category}
            currentProbability={event.currentProbability}
            previousProbability={event.previousProbability}
          />
        </CardHeader>
        <CardContent className="space-y-3">
          <MiniSparkline data={history ?? []} loading={historyLoading} />
          <Separator />
          <EventImpacts impacts={event.impacts} compact />
          <Separator />
          <ImpliedFinancials financials={event.impliedFinancials} compact />
        </CardContent>
      </Card>
    </Link>
  );
}
