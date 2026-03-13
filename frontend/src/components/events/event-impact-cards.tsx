"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useEventImpacts } from "@/hooks/use-impacts";
import { DollarSign, TrendingDown } from "lucide-react";

function formatDollars(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(0)}`;
}

interface EventImpactCardsProps {
  eventId: string;
}

export function EventImpactCards({ eventId }: EventImpactCardsProps) {
  const { data: impacts, isLoading } = useEventImpacts(eventId);

  if (isLoading) {
    return (
      <div className="grid gap-6 lg:grid-cols-2">
        <Skeleton className="h-48 w-full" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!impacts || impacts.length === 0) return null;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Table 1: Event Impacts (OPEX + CAPEX per day) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <DollarSign className="h-4 w-4 text-orange-500" />
            Event Impacts
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Daily cost exposure by company
          </p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Company</th>
                  <th className="pb-2 font-medium text-right">OPEX/day</th>
                  <th className="pb-2 font-medium text-right">CAPEX/day</th>
                  <th className="pb-2 font-medium text-right">Total/day</th>
                </tr>
              </thead>
              <tbody>
                {impacts.map((impact) => (
                  <tr key={impact.companyId} className="border-b last:border-0">
                    <td className="py-2 font-medium">{impact.companyName}</td>
                    <td className="py-2 text-right text-orange-600">
                      {formatDollars(impact.opexImpactPerDay)}
                    </td>
                    <td className="py-2 text-right text-orange-600">
                      {formatDollars(impact.capexImpactPerDay)}
                    </td>
                    <td className="py-2 text-right font-semibold text-red-600">
                      {formatDollars(impact.opexImpactPerDay + impact.capexImpactPerDay)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Table 2: Implied Company Financials Move */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <TrendingDown className="h-4 w-4 text-red-500" />
            Implied Company Financials Move
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            With vs without this event
          </p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="pb-2 font-medium">Company</th>
                  <th className="pb-2 font-medium text-right">Revenue</th>
                  <th className="pb-2 font-medium text-right">OPEX</th>
                  <th className="pb-2 font-medium text-right">CAPEX</th>
                  <th className="pb-2 font-medium text-right">Net Impact</th>
                </tr>
              </thead>
              <tbody>
                {impacts.map((impact) => (
                  <tr key={impact.companyId} className="border-b last:border-0">
                    <td className="py-2 font-medium">{impact.companyName}</td>
                    <td className="py-2 text-right text-red-600">
                      {formatDollars(impact.revenueImpactPerDay)}
                    </td>
                    <td className="py-2 text-right text-orange-600">
                      {formatDollars(impact.opexImpactPerDay)}
                    </td>
                    <td className="py-2 text-right text-orange-600">
                      {formatDollars(impact.capexImpactPerDay)}
                    </td>
                    <td className="py-2 text-right font-semibold text-red-600">
                      {formatDollars(impact.totalImpactPerDay)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
