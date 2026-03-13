"use client";

import { use } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

import { CurrencyDisplay } from "@/components/shared/currency-display";
import { CompanyExposureTable } from "@/components/companies/company-exposure-table";
import { RiskScoreBadge } from "@/components/risk/risk-score-badge";
import { useCompany, useCompanyExposures } from "@/hooks/use-companies";
import { useCompanyRisk } from "@/hooks/use-risk";
import { Skeleton } from "@/components/ui/skeleton";

export default function CompanyDetailPage({
  params,
}: {
  params: Promise<{ companyId: string }>;
}) {
  const { companyId } = use(params);
  const { data: company, isLoading: loadingCompany } = useCompany(companyId);
  const { data: exposures, isLoading: loadingExposures } = useCompanyExposures(companyId);
  const { data: riskData } = useCompanyRisk(companyId);

  if (loadingCompany) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full" />
      </div>
    );
  }

  if (!company) {
    return <p className="text-muted-foreground py-12 text-center">Company not found.</p>;
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">{company.name}</h1>
        <Badge variant="outline" className="font-mono text-sm">
          {company.ticker}
        </Badge>
        <span className="text-sm text-muted-foreground">{company.sector} sector</span>
        {riskData && <RiskScoreBadge score={riskData.riskScore} />}
      </div>

      <div className="grid gap-5 sm:grid-cols-4">
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Market Cap</p>
            <CurrencyDisplay value={company.marketCap} className="text-xl font-semibold" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Annual Revenue</p>
            <CurrencyDisplay value={company.annualRevenue} className="text-xl font-semibold" />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Active Exposures</p>
            <p className="text-xl font-semibold font-mono">{company.exposureCount}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground">Risk Score</p>
            <RiskScoreBadge score={riskData?.riskScore ?? null} size="lg" />
            {riskData && riskData.eventCount > 0 && (
              <p className="text-xs text-muted-foreground mt-1">
                {riskData.eventCount} matched event{riskData.eventCount !== 1 ? "s" : ""}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Exposure Profile</CardTitle>
        </CardHeader>
        <CardContent>
          {loadingExposures ? (
            <Skeleton className="h-48 w-full" />
          ) : exposures && exposures.length > 0 ? (
            <CompanyExposureTable exposures={exposures} />
          ) : (
            <p className="text-sm text-muted-foreground py-4">No exposures mapped.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
