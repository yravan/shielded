"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { CurrencyDisplay } from "@/components/shared/currency-display";
import { cn } from "@/lib/utils";
import type { FinancialImpact } from "@/types";

interface FinancialImpactsProps {
  impacts: FinancialImpact[];
}

function ImpactCell({ value, suffix = "%" }: { value: number; suffix?: string }) {
  return (
    <span
      className={cn(
        "font-mono text-xs font-medium",
        value < 0 ? "text-red-400" : value > 0 ? "text-emerald-400" : "text-muted-foreground"
      )}
    >
      {value > 0 ? "+" : ""}
      {value.toFixed(1)}
      {suffix}
    </span>
  );
}

export function FinancialImpacts({ impacts }: FinancialImpactsProps) {
  if (!impacts || impacts.length === 0) return null;

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Company</TableHead>
            <TableHead className="text-right">Revenue Impact</TableHead>
            <TableHead className="text-right">OPEX Impact</TableHead>
            <TableHead className="text-right">CAPEX Impact</TableHead>
            <TableHead className="text-right">Net Income</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {impacts.map((impact) => (
            <TableRow key={impact.ticker}>
              <TableCell>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-muted-foreground">
                    {impact.ticker}
                  </span>
                  <span className="text-sm">{impact.companyName}</span>
                </div>
              </TableCell>
              <TableCell className="text-right">
                <div className="flex flex-col items-end gap-0.5">
                  <ImpactCell value={impact.revenueImpactPercent} />
                  <CurrencyDisplay
                    value={Math.abs(impact.revenueAtRisk)}
                    className="text-[10px] text-muted-foreground"
                  />
                </div>
              </TableCell>
              <TableCell className="text-right">
                <div className="flex flex-col items-end gap-0.5">
                  <ImpactCell value={impact.opexImpactPercent} />
                  <CurrencyDisplay
                    value={Math.abs(impact.opexAtRisk)}
                    className="text-[10px] text-muted-foreground"
                  />
                </div>
              </TableCell>
              <TableCell className="text-right">
                <div className="flex flex-col items-end gap-0.5">
                  <ImpactCell value={impact.capexImpactPercent} />
                  <CurrencyDisplay
                    value={Math.abs(impact.capexAtRisk)}
                    className="text-[10px] text-muted-foreground"
                  />
                </div>
              </TableCell>
              <TableCell className="text-right">
                <ImpactCell value={impact.netIncomeImpactPercent} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
