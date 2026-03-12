"use client";

import { PageHeader } from "@/components/shared/page-header";
import { CompanyCard } from "@/components/companies/company-card";
import { useCompanies } from "@/hooks/use-companies";
import { Skeleton } from "@/components/ui/skeleton";

export default function CompaniesPage() {
  const { data: companies, isLoading } = useCompanies();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Companies"
        description="Track company exposure to geopolitical events"
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-48 w-full rounded-lg" />
            ))
          : companies?.map((company) => (
              <CompanyCard key={company.id} company={company} />
            ))}
      </div>
    </div>
  );
}
