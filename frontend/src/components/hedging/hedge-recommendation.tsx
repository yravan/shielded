"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { CurrencyDisplay } from "@/components/shared/currency-display";
import type { HedgeComparison } from "@/types";

interface HedgeRecommendationProps {
  comparison: HedgeComparison;
}

const recommendationColors: Record<string, string> = {
  prediction_market: "bg-primary/15 text-primary border-primary/30",
  traditional: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  blend: "bg-purple-500/15 text-purple-400 border-purple-500/30",
  no_hedge: "bg-muted text-muted-foreground border-border",
};

const recommendationLabels: Record<string, string> = {
  prediction_market: "Prediction Market",
  traditional: "Traditional",
  blend: "Blended Strategy",
  no_hedge: "No Hedge Needed",
};

export function HedgeRecommendation({ comparison }: HedgeRecommendationProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-base">{comparison.eventTitle}</CardTitle>
            <p className="text-xs text-muted-foreground mt-0.5">{comparison.companyName}</p>
          </div>
          <Badge variant="outline" className={recommendationColors[comparison.recommendation]}>
            {recommendationLabels[comparison.recommendation]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Prediction Market
            </p>
            <div className="space-y-1.5">
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground shrink-0">Platform</span>
                <span className="text-xs text-right truncate max-w-[200px]">{comparison.predictionMarket.platform}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground shrink-0">Instrument</span>
                <span className="text-xs text-right truncate max-w-[200px]">{comparison.predictionMarket.instrument}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground">Cost</span>
                <CurrencyDisplay value={comparison.predictionMarket.cost} className="text-xs" />
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground">Payout</span>
                <CurrencyDisplay value={comparison.predictionMarket.payout} className="text-xs" />
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground">ROI</span>
                <span className="text-xs font-mono text-emerald-400">
                  {(comparison.predictionMarket.roi * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
              Traditional
            </p>
            <div className="space-y-1.5">
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground shrink-0">Provider</span>
                <span className="text-xs text-right truncate max-w-[200px]">{comparison.traditional.provider}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground shrink-0">Instrument</span>
                <span className="text-xs text-right truncate max-w-[200px]">{comparison.traditional.instrument}</span>
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground">Cost</span>
                <CurrencyDisplay value={comparison.traditional.cost} className="text-xs" />
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground">Payout</span>
                <CurrencyDisplay value={comparison.traditional.payout} className="text-xs" />
              </div>
              <div className="flex justify-between gap-4">
                <span className="text-xs text-muted-foreground">ROI</span>
                <span className="text-xs font-mono text-muted-foreground">
                  {(comparison.traditional.roi * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <Separator className="my-3" />

        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">PM Cost Savings</span>
          <span className="text-sm font-mono font-semibold text-emerald-400">
            {comparison.savingsPercent.toFixed(0)}%
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
