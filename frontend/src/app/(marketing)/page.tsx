"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Shield, BarChart3, Globe, Scale } from "lucide-react";

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

export default function LandingPage() {
  return (
    <>
      <section className="relative pt-32 pb-20 px-6">
        <div className="mx-auto max-w-4xl text-center">
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
            <Link href="/dashboard" className={cn(buttonVariants({ size: "lg" }))}>
              Get Started
            </Link>
            <Link href="#features" className={cn(buttonVariants({ size: "lg", variant: "outline" }))}>
              Learn More
            </Link>
          </div>
        </div>
      </section>

      <section id="features" className="py-20 px-6">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-center text-2xl font-semibold tracking-tight mb-12">
            Everything you need to manage geopolitical risk
          </h2>
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

      <section id="how-it-works" className="py-20 px-6 border-t border-border">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="text-2xl font-semibold tracking-tight mb-4">How It Works</h2>
          <p className="text-muted-foreground mb-12">
            Three steps to smarter geopolitical risk management
          </p>
          <div className="grid gap-8 sm:grid-cols-3">
            {[
              { step: "1", title: "Monitor", desc: "Track geopolitical events with real-time probability data" },
              { step: "2", title: "Analyze", desc: "Map your company's financial exposure to each event" },
              { step: "3", title: "Hedge", desc: "Compare PM vs traditional hedges and execute the best strategy" },
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
          <Link href="/dashboard" className={cn(buttonVariants({ size: "lg" }), "mt-12")}>
            Start Hedging
          </Link>
        </div>
      </section>
    </>
  );
}
