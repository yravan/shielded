"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

import { HedgeRecommendation } from "@/components/hedging/hedge-recommendation";
import { MarketComparison } from "@/components/hedging/market-comparison";
import { useHedgeComparisons } from "@/hooks/use-hedging";
import { Skeleton } from "@/components/ui/skeleton";

export default function HedgingPage() {
  const { data: comparisons, isLoading } = useHedgeComparisons();

  return (
    <div className="space-y-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Cost Comparison</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-[350px] w-full" />
          ) : comparisons ? (
            <MarketComparison comparisons={comparisons} />
          ) : null}
        </CardContent>
      </Card>

      <h2 className="text-lg font-semibold">Hedge Recommendations</h2>
      <div className="grid gap-5 lg:grid-cols-2">
        {isLoading
          ? Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-64 w-full rounded-lg" />
            ))
          : comparisons?.map((c) => (
              <HedgeRecommendation key={c.id} comparison={c} />
            ))}
      </div>
    </div>
  );
}
