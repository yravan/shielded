"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CurrencyDisplay } from "@/components/shared/currency-display";
import type { Company } from "@/types";

interface CompanyCardProps {
  company: Company;
}

export function CompanyCard({ company }: CompanyCardProps) {
  return (
    <Link href={`/companies/${company.id}`}>
      <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base">{company.name}</CardTitle>
            <Badge variant="outline" className="font-mono text-xs">
              {company.ticker}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">{company.sector}</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-muted-foreground">Market Cap</p>
              <CurrencyDisplay value={company.marketCap} className="text-sm" />
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Revenue</p>
              <CurrencyDisplay value={company.annualRevenue} className="text-sm" />
            </div>
          </div>
          <div className="mt-3">
            <Badge variant="secondary" className="text-xs">
              {company.exposureCount} exposures
            </Badge>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
