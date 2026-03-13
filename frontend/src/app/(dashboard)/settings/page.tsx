"use client";

import { useState, useEffect } from "react";
import { useTheme } from "next-themes";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { useMyCompanies, useSaveCompany, useUpdateCompany, useDeleteCompany, useCompanyLookup } from "@/hooks/use-company";
import { Badge } from "@/components/ui/badge";
import { Building2, Loader2, Check, Plus, Pencil, Trash2, X } from "lucide-react";
import type { UserCompany } from "@/types";

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

interface CompanyFormProps {
  initial?: UserCompany | null;
  onSave: (data: {
    name: string;
    ticker: string | null;
    sector: string;
    annual_revenue: number;
    operating_expense: number;
    capital_expense: number;
  }) => Promise<void>;
  onCancel: () => void;
  isPending: boolean;
}

function formatRevenue(value: number): string {
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(0)}K`;
  return String(value);
}

function CompanyForm({ initial, onSave, onCancel, isPending }: CompanyFormProps) {
  const [name, setName] = useState(initial?.name ?? "");
  const [ticker, setTicker] = useState(initial?.ticker ?? "");
  const [lookupTicker, setLookupTicker] = useState("");
  const [sector, setSector] = useState(initial?.sector ?? "");
  const [annualRevenue, setAnnualRevenue] = useState(initial?.annualRevenue ? String(initial.annualRevenue) : "");
  const [operatingExpense, setOperatingExpense] = useState(initial?.operatingExpense ? String(initial.operatingExpense) : "");
  const [capitalExpense, setCapitalExpense] = useState(initial?.capitalExpense ? String(initial.capitalExpense) : "");
  const [showSuggestion, setShowSuggestion] = useState(false);

  const { data: lookup, isFetching: lookingUp } = useCompanyLookup(lookupTicker);

  // Debounced ticker lookup on input change
  useEffect(() => {
    if (!ticker || ticker.length < 1 || ticker === (initial?.ticker ?? "")) {
      setShowSuggestion(false);
      return;
    }
    const timer = setTimeout(() => setLookupTicker(ticker), 500);
    return () => clearTimeout(timer);
  }, [ticker, initial?.ticker]);

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
    if (lookup.operatingExpense != null) setOperatingExpense(String(Math.round(lookup.operatingExpense)));
    if (lookup.capitalExpense != null) setCapitalExpense(String(Math.abs(Math.round(lookup.capitalExpense))));
    setShowSuggestion(false);
  };

  const handleSubmit = async () => {
    await onSave({
      name,
      ticker: ticker || null,
      sector,
      annual_revenue: parseFloat(annualRevenue) || 0,
      operating_expense: parseFloat(operatingExpense) || 0,
      capital_expense: parseFloat(capitalExpense) || 0,
    });
  };

  return (
    <div className="space-y-4 rounded-lg border p-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Company Name</Label>
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Acme Corp" />
        </div>
        <div className="space-y-2">
          <Label>Ticker</Label>
          <div className="relative">
            <Input
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              onBlur={() => {
                // Delay dismiss so click on suggestion can fire first
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
                  {lookup.annualRevenue != null && <> &middot; Rev ${formatRevenue(lookup.annualRevenue)}</>}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="space-y-2">
        <Label>Sector</Label>
        <Select value={sector} onValueChange={(v) => setSector(v ?? "")}>
          <SelectTrigger>
            <SelectValue placeholder="Select a sector" />
          </SelectTrigger>
          <SelectContent>
            {sectors.map((s) => (
              <SelectItem key={s} value={s}>{s}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-2">
          <Label>Annual Revenue ($)</Label>
          <Input type="number" value={annualRevenue} onChange={(e) => setAnnualRevenue(e.target.value)} className="font-mono text-sm" />
        </div>
        <div className="space-y-2">
          <Label>Operating Expenses ($)</Label>
          <Input type="number" value={operatingExpense} onChange={(e) => setOperatingExpense(e.target.value)} className="font-mono text-sm" />
        </div>
        <div className="space-y-2">
          <Label>Capital Expenses ($)</Label>
          <Input type="number" value={capitalExpense} onChange={(e) => setCapitalExpense(e.target.value)} className="font-mono text-sm" />
        </div>
      </div>
      <div className="flex gap-2">
        <Button onClick={handleSubmit} disabled={!name.trim() || !sector || isPending}>
          {isPending ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Saving...</>
          ) : (
            initial ? "Update Company" : "Add Company"
          )}
        </Button>
        <Button variant="ghost" onClick={onCancel}>
          <X className="mr-1 h-4 w-4" />Cancel
        </Button>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { data: companies, isLoading: companiesLoading } = useMyCompanies();
  const saveCompany = useSaveCompany();
  const updateCompany = useUpdateCompany();
  const deleteCompany = useDeleteCompany();

  const [showAddForm, setShowAddForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const handleAdd = async (data: Parameters<CompanyFormProps["onSave"]>[0]) => {
    await saveCompany.mutateAsync(data);
    setShowAddForm(false);
  };

  const handleUpdate = async (id: string, data: Parameters<CompanyFormProps["onSave"]>[0]) => {
    await updateCompany.mutateAsync({ id, data });
    setEditingId(null);
  };

  const handleDelete = async (id: string) => {
    await deleteCompany.mutateAsync(id);
  };

  return (
    <div className="space-y-8">
      {/* Companies */}
      <Card className="max-w-2xl">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-base flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                My Companies
              </CardTitle>
              <CardDescription>
                Companies used for risk exposure analysis
              </CardDescription>
            </div>
            {!showAddForm && (
              <Button variant="outline" size="sm" onClick={() => setShowAddForm(true)}>
                <Plus className="mr-1 h-4 w-4" />Add Company
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {companiesLoading ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : (
            <>
              {companies?.length === 0 && !showAddForm && (
                <p className="text-sm text-muted-foreground">No companies added yet.</p>
              )}
              {companies?.map((company) => (
                <div key={company.id}>
                  {editingId === company.id ? (
                    <CompanyForm
                      initial={company}
                      onSave={(data) => handleUpdate(company.id, data)}
                      onCancel={() => setEditingId(null)}
                      isPending={updateCompany.isPending}
                    />
                  ) : (
                    <div className="flex items-center justify-between rounded-lg border p-4">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{company.name}</span>
                          {company.ticker && (
                            <Badge variant="outline" className="font-mono text-[10px]">
                              {company.ticker}
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {company.sector}
                          {company.annualRevenue > 0 && (
                            <> &middot; Rev ${(company.annualRevenue / 1e9).toFixed(1)}B</>
                          )}
                        </p>
                      </div>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" onClick={() => setEditingId(company.id)}>
                          <Pencil className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(company.id)}
                          disabled={deleteCompany.isPending}
                        >
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {showAddForm && (
                <CompanyForm
                  onSave={handleAdd}
                  onCancel={() => setShowAddForm(false)}
                  isPending={saveCompany.isPending}
                />
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Appearance */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="text-base">Appearance</CardTitle>
          <CardDescription>Customize how the dashboard looks</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="dark-mode">Dark Mode</Label>
              <p className="text-xs text-muted-foreground">
                Use dark theme for the interface
              </p>
            </div>
            <Switch
              id="dark-mode"
              checked={theme === "dark"}
              onCheckedChange={(checked) => setTheme(checked ? "dark" : "light")}
            />
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="text-base">Notifications</CardTitle>
          <CardDescription>Choose what alerts you receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="prob-alerts">Probability Alerts</Label>
              <p className="text-xs text-muted-foreground">
                Notify when an event probability changes by more than 5%
              </p>
            </div>
            <Switch id="prob-alerts" defaultChecked />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="new-events">New Event Discovery</Label>
              <p className="text-xs text-muted-foreground">
                Notify when new geopolitical events are detected
              </p>
            </div>
            <Switch id="new-events" defaultChecked />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="hedge-updates">Hedge Recommendation Updates</Label>
              <p className="text-xs text-muted-foreground">
                Notify when hedge recommendations change for tracked companies
              </p>
            </div>
            <Switch id="hedge-updates" defaultChecked />
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label htmlFor="resolution-alerts">Event Resolution</Label>
              <p className="text-xs text-muted-foreground">
                Notify when tracked events resolve or expire
              </p>
            </div>
            <Switch id="resolution-alerts" defaultChecked />
          </div>
        </CardContent>
      </Card>

      {/* Data Sources */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="text-base">Data Sources</CardTitle>
          <CardDescription>
            Prediction market data feeds configured by the server administrator
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Polymarket</Label>
              <p className="text-xs text-muted-foreground">
                Public prediction market — no API key required
              </p>
            </div>
            <Badge variant="outline" className="text-[10px] bg-emerald-500/15 text-emerald-400 border-emerald-500/30">
              Active
            </Badge>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label>Kalshi</Label>
              <p className="text-xs text-muted-foreground">
                Regulated prediction market — RSA-signed API
              </p>
            </div>
            <Badge variant="outline" className="text-[10px] bg-emerald-500/15 text-emerald-400 border-emerald-500/30">
              Active
            </Badge>
          </div>
          <Separator />
          <div className="flex items-center justify-between">
            <div>
              <Label>Metaculus</Label>
              <p className="text-xs text-muted-foreground">
                Community forecasting platform
              </p>
            </div>
            <Badge variant="outline" className="text-[10px]">
              Not configured
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* API Keys — disabled */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="text-base">API Keys</CardTitle>
          <CardDescription>
            API keys are configured by the server administrator. Contact your admin to change data source credentials.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="kalshi-key">Kalshi API Key</Label>
            <Input
              id="kalshi-key"
              type="password"
              value="****configured****"
              disabled
              className="font-mono text-sm opacity-60"
            />
            <p className="text-xs text-muted-foreground">Configured by server administrator</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="metaculus-key">Metaculus API Key</Label>
            <Input
              id="metaculus-key"
              type="password"
              value=""
              placeholder="Not configured"
              disabled
              className="font-mono text-sm opacity-60"
            />
            <p className="text-xs text-muted-foreground">Configured by server administrator</p>
          </div>
        </CardContent>
      </Card>

      {/* Polling Configuration */}
      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="text-base">Data Refresh</CardTitle>
          <CardDescription>
            Live polling is enabled server-side. Events are discovered hourly and probabilities updated every 5 minutes.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <Label>Live Polling</Label>
              <p className="text-xs text-muted-foreground">
                Automatically fetching updated probabilities from markets
              </p>
            </div>
            <Badge variant="outline" className="text-[10px] bg-emerald-500/15 text-emerald-400 border-emerald-500/30">
              Enabled
            </Badge>
          </div>
          <Separator />
          <div className="space-y-2">
            <Label>Poll Interval</Label>
            <p className="text-sm font-mono">300s (5 minutes)</p>
            <p className="text-xs text-muted-foreground">
              Configured server-side via POLL_INTERVAL_SECONDS
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
