"use client";

import Link from "next/link";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { CurrencyDisplay } from "@/components/shared/currency-display";
import type { CompanyExposure } from "@/types";
import { cn } from "@/lib/utils";

interface CompanyExposureTableProps {
  exposures: CompanyExposure[];
}

const directionColors = {
  negative: "text-red-400",
  positive: "text-emerald-400",
  mixed: "text-yellow-400",
};

const recommendationLabels: Record<string, string> = {
  prediction_market: "PM Hedge",
  traditional: "Traditional",
  blend: "Blended",
  no_hedge: "No Hedge",
};

export function CompanyExposureTable({ exposures }: CompanyExposureTableProps) {
  return (
    <div className="overflow-x-auto">
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Event</TableHead>
          <TableHead>Type</TableHead>
          <TableHead>Direction</TableHead>
          <TableHead className="text-right">Revenue at Risk</TableHead>
          <TableHead>Recommendation</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {exposures.map((exposure) => (
          <TableRow key={exposure.id}>
            <TableCell>
              <Link
                href={`/events/${exposure.eventId}`}
                className="text-primary hover:underline"
              >
                {exposure.eventTitle}
              </Link>
            </TableCell>
            <TableCell className="capitalize text-sm">
              {exposure.exposureType.replace("_", " ")}
            </TableCell>
            <TableCell>
              <span className={cn("text-sm capitalize", directionColors[exposure.exposureDirection])}>
                {exposure.exposureDirection}
              </span>
            </TableCell>
            <TableCell className="text-right">
              <CurrencyDisplay value={exposure.revenueAtRisk} className="text-sm" />
              <span className="ml-1 text-xs text-muted-foreground">
                ({exposure.revenueAtRiskPercent.toFixed(1)}%)
              </span>
            </TableCell>
            <TableCell>
              <Badge variant="outline" className="text-xs">
                {recommendationLabels[exposure.hedgeRecommendation] ?? exposure.hedgeRecommendation}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
    </div>
  );
}
