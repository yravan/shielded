"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, BarChart3, Globe, Scale, TrendingDown, Building2, Activity, Zap } from "lucide-react";

const features = [
  {
    icon: Globe,
    title: "Real-Time Event Tracking",
    description:
      "Monitor geopolitical events with live probability data from prediction markets like Polymarket, Kalshi, and Metaculus.",
  },
  {
    icon: BarChart3,
    title: "Exposure Mapping",
    description:
      "Map your company's financial exposure to geopolitical events across revenue, supply chain, and operations.",
  },
  {
    icon: Scale,
    title: "Hedge Comparison",
    description:
      "Compare prediction market hedges against traditional instruments like FX forwards, options, and futures.",
  },
  {
    icon: Shield,
    title: "Cost Savings",
    description:
      "Discover 15-40% cost savings by using prediction markets as an alternative hedging mechanism.",
  },
];

const stats = [
  { value: "8+", label: "Geopolitical Events Tracked", icon: Activity },
  { value: "28%", label: "Average Hedging Cost Savings", icon: TrendingDown },
  { value: "5", label: "Major Companies Covered", icon: Building2 },
  { value: "3", label: "Prediction Market Sources", icon: Zap },
];

const useCases = [
  {
    company: "Energy Companies",
    description: "Hedge against supply disruptions in the Strait of Hormuz or OPEC production changes using PM contracts at 31% lower cost than crude options.",
    savings: "31%",
    event: "Iran Strait of Hormuz Disruption",
  },
  {
    company: "Semiconductor Firms",
    description: "Protect against China-Taiwan escalation risk. PM binary contracts offer 16x ROI vs 11.5x for traditional ETF puts.",
    savings: "29%",
    event: "China-Taiwan Military Escalation",
  },
  {
    company: "Shipping & Logistics",
    description: "Manage Red Sea shipping disruption exposure. PM hedges cost 29% less than freight derivatives for equivalent coverage.",
    savings: "29%",
    event: "Red Sea Shipping Disruption",
  },
];

export default function LandingPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative pt-32 pb-20 px-6">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,oklch(0.35_0.15_250),transparent_70%)] opacity-30" />
        <div className="mx-auto max-w-4xl text-center">
          <Badge variant="outline" className="mb-6 px-4 py-1.5 text-sm">
            The Fama-French Model for Geopolitical Risk
          </Badge>
          <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
            Hedge Geopolitical Risk{" "}
            <span className="text-primary">Smarter</span>
          </h1>
          <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
            Shielded maps your company&apos;s exposure to geopolitical events and compares
            prediction market hedges against traditional financial instruments — saving
            you 15-40% on hedging costs.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link href="/onboarding" className={cn(buttonVariants({ size: "lg" }))}>
              Get Started
            </Link>
            <Link href="#features" className={cn(buttonVariants({ size: "lg", variant: "outline" }))}>
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 px-6 border-t border-border">
        <div className="mx-auto max-w-6xl">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <stat.icon className="h-5 w-5 text-primary mx-auto mb-2" />
                <p className="text-3xl font-bold font-mono text-primary">{stat.value}</p>
                <p className="mt-1 text-sm text-muted-foreground">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-6">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-2xl font-semibold tracking-tight mb-4">
            Everything you need to manage geopolitical risk
          </h2>
          <p className="text-center text-muted-foreground mb-12 max-w-2xl mx-auto">
            From event detection to hedge execution — one platform for systematic geopolitical risk management.
          </p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature) => (
              <Card key={feature.title} className="bg-card/50 h-full">
                <CardContent className="pt-6">
                  <feature.icon className="h-7 w-7 text-primary mb-3" />
                  <h3 className="font-semibold mb-1">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-20 px-6 border-t border-border">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-2xl font-semibold tracking-tight mb-4">
            Real-World Use Cases
          </h2>
          <p className="text-center text-muted-foreground mb-12">
            See how prediction market hedges outperform traditional instruments
          </p>
          <div className="grid gap-6 lg:grid-cols-3">
            {useCases.map((uc) => (
              <Card key={uc.company} className="h-full">
                <CardContent className="pt-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold">{uc.company}</h3>
                    <Badge variant="outline" className="bg-emerald-500/15 text-emerald-400 border-emerald-500/30 font-mono">
                      {uc.savings} saved
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{uc.description}</p>
                  <Badge variant="secondary" className="text-xs">
                    {uc.event}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-6 border-t border-border">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-semibold tracking-tight mb-4">How It Works</h2>
          <p className="text-muted-foreground mb-12">
            Three steps to smarter geopolitical risk management
          </p>
          <div className="grid gap-8 sm:grid-cols-3">
            {[
              { step: "1", title: "Monitor", desc: "Track geopolitical events with real-time probability data from multiple prediction markets" },
              { step: "2", title: "Analyze", desc: "Map your company's financial exposure — revenue, OPEX, and CAPEX impacts per event" },
              { step: "3", title: "Hedge", desc: "Compare PM vs traditional hedges, see the cost savings, and execute the optimal strategy" },
            ].map((item) => (
              <div key={item.step}>
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold">
                  {item.step}
                </div>
                <h3 className="font-semibold">{item.title}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{item.desc}</p>
              </div>
            ))}
          </div>
          <Link href="/onboarding" className={cn(buttonVariants({ size: "lg" }), "mt-12")}>
            Start Hedging
          </Link>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-border">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-2xl font-semibold tracking-tight mb-4">
            Ready to reduce your hedging costs?
          </h2>
          <p className="text-muted-foreground mb-8">
            Join the companies using prediction markets for smarter, cheaper geopolitical risk management.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link href="/onboarding" className={cn(buttonVariants({ size: "lg" }))}>
              Get Started Free
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
