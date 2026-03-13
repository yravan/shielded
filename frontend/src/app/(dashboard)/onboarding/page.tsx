"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useSaveCompany, useCompanyLookup } from "@/hooks/use-company";
import { Building2, Loader2 } from "lucide-react";

const sectors = [
  "Energy",
  "Materials",
  "Industrials",
  "Consumer Discretionary",
  "Consumer Staples",
  "Healthcare",
  "Financials",
  "Information Technology",
  "Communication Services",
  "Utilities",
  "Real Estate",
  "Other",
];

export default function OnboardingPage() {
  const router = useRouter();
  const saveCompany = useSaveCompany();

  const [name, setName] = useState("");
  const [ticker, setTicker] = useState("");
  const [lookupTicker, setLookupTicker] = useState("");
  const [sector, setSector] = useState("");
  const [annualRevenue, setAnnualRevenue] = useState("");
  const [operatingExpense, setOperatingExpense] = useState("");
  const [capitalExpense, setCapitalExpense] = useState("");

  const [showSuggestion, setShowSuggestion] = useState(false);
  const { data: lookup, isFetching: lookingUp } = useCompanyLookup(lookupTicker);

  // Debounced ticker lookup on input change
  useEffect(() => {
    if (!ticker || ticker.length < 1) {
      setShowSuggestion(false);
      return;
    }
    const timer = setTimeout(() => setLookupTicker(ticker), 500);
    return () => clearTimeout(timer);
  }, [ticker]);

  // Show suggestion card when lookup data arrives
  useEffect(() => {
    if (lookup && lookupTicker) {
      setShowSuggestion(true);
    }
  }, [lookup, lookupTicker]);

  const applySuggestion = () => {
    if (!lookup) return;
    if (lookup.name) setName(lookup.name);
    if (lookup.sector) setSector(lookup.sector);
    if (lookup.annualRevenue != null) setAnnualRevenue(String(Math.round(lookup.annualRevenue)));
    if (lookup.operatingExpense != null)
      setOperatingExpense(String(Math.round(lookup.operatingExpense)));
    if (lookup.capitalExpense != null)
      setCapitalExpense(String(Math.abs(Math.round(lookup.capitalExpense))));
    setShowSuggestion(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await saveCompany.mutateAsync({
      name,
      ticker: ticker || null,
      sector,
      annual_revenue: parseFloat(annualRevenue) || 0,
      operating_expense: parseFloat(operatingExpense) || 0,
      capital_expense: parseFloat(capitalExpense) || 0,
    });
    router.push("/dashboard");
  };

  const isValid = name.trim() && sector;

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Building2 className="h-4 w-4" />
            Company Information
          </CardTitle>
          <CardDescription>
            Enter your company details manually, or type a public ticker to auto-fill financials
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="name">Company Name *</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Acme Corp"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="ticker">Ticker (optional)</Label>
                <div className="relative">
                  <Input
                    id="ticker"
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    onBlur={() => {
                      setTimeout(() => setShowSuggestion(false), 200);
                    }}
                    placeholder="AAPL"
                    className="font-mono"
                  />
                  {lookingUp && (
                    <Loader2 className="absolute right-3 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                  {showSuggestion && lookup && (
                    <div
                      className="absolute z-10 mt-1 w-full rounded-md border bg-popover p-3 shadow-md cursor-pointer hover:bg-accent transition-colors"
                      onClick={applySuggestion}
                    >
                      <p className="font-medium text-sm">{lookup.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {lookup.sector}
                        {lookup.annualRevenue != null && (
                          <> &middot; Rev ${(lookup.annualRevenue >= 1e9
                            ? `${(lookup.annualRevenue / 1e9).toFixed(1)}B`
                            : lookup.annualRevenue >= 1e6
                              ? `${(lookup.annualRevenue / 1e6).toFixed(1)}M`
                              : String(lookup.annualRevenue))}</>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sector">Sector *</Label>
              <Select value={sector} onValueChange={(v) => setSector(v ?? "")}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a sector" />
                </SelectTrigger>
                <SelectContent>
                  {sectors.map((s) => (
                    <SelectItem key={s} value={s}>
                      {s}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="revenue">Annual Revenue ($)</Label>
                <Input
                  id="revenue"
                  type="number"
                  value={annualRevenue}
                  onChange={(e) => setAnnualRevenue(e.target.value)}
                  placeholder="1000000"
                  className="font-mono text-sm"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="opex">Operating Expenses ($)</Label>
                <Input
                  id="opex"
                  type="number"
                  value={operatingExpense}
                  onChange={(e) => setOperatingExpense(e.target.value)}
                  placeholder="500000"
                  className="font-mono text-sm"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="capex">Capital Expenses ($)</Label>
                <Input
                  id="capex"
                  type="number"
                  value={capitalExpense}
                  onChange={(e) => setCapitalExpense(e.target.value)}
                  placeholder="100000"
                  className="font-mono text-sm"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={!isValid || saveCompany.isPending}
              className="w-full"
            >
              {saveCompany.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save & Continue"
              )}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
