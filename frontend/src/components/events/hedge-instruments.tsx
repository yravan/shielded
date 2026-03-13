"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api-client";
import { Shield } from "lucide-react";
import type { HedgeInstrument } from "@/types";
import { useMatchedCompanies } from "@/hooks/use-risk";

/* eslint-disable @typescript-eslint/no-explicit-any */

async function fetchHedgeInstruments(
  companyId: string,
  eventId: string
): Promise<HedgeInstrument[]> {
  const res = await apiFetch(
    `/api/hedge-analysis?company_id=${companyId}&event_id=${eventId}`
  );
  if (!res.ok) return [];
  const data = await res.json();
  return (data.suggested_instruments ?? []).map((i: any) => ({
    ticker: i.ticker,
    instrumentType: i.instrument_type,
    direction: i.direction,
    rationale: i.rationale,
  }));
}

function InstrumentsTable({ instruments }: { instruments: HedgeInstrument[] }) {
  const directionColor: Record<string, string> = {
    long: "text-emerald-600",
    short: "text-red-600",
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="pb-2 font-medium">Ticker</th>
            <th className="pb-2 font-medium">Type</th>
            <th className="pb-2 font-medium">Direction</th>
            <th className="pb-2 font-medium">Rationale</th>
          </tr>
        </thead>
        <tbody>
          {instruments.map((inst, i) => (
            <tr key={`${inst.ticker}-${i}`} className="border-b last:border-0">
              <td className="py-2 font-mono font-medium">{inst.ticker}</td>
              <td className="py-2">
                <Badge variant="outline" className="text-xs">
                  {inst.instrumentType}
                </Badge>
              </td>
              <td className={`py-2 font-medium ${directionColor[inst.direction] ?? ""}`}>
                {inst.direction.toUpperCase()}
              </td>
              <td className="py-2 text-muted-foreground">{inst.rationale}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function HedgeInstrumentsSection({ eventId }: { eventId: string }) {
  const { data: matched, isLoading: matchLoading } = useMatchedCompanies(eventId);

  // Use the first matched company to get hedge instruments
  const firstCompanyId = matched?.[0]?.companyId;

  const { data: instruments, isLoading: hedgeLoading } = useQuery({
    queryKey: ["hedge-instruments", eventId, firstCompanyId],
    queryFn: () => fetchHedgeInstruments(firstCompanyId!, eventId),
    enabled: !!firstCompanyId,
  });

  if (matchLoading || hedgeLoading) {
    return <Skeleton className="h-32 w-full" />;
  }

  if (!instruments || instruments.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          <Shield className="h-4 w-4 text-blue-500" />
          Suggested Hedge Instruments
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Theme-based instrument recommendations for hedging this event
        </p>
      </CardHeader>
      <CardContent>
        <InstrumentsTable instruments={instruments} />
      </CardContent>
    </Card>
  );
}
