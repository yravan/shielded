"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4">
      <h1 className="text-6xl font-bold font-mono text-primary">404</h1>
      <h2 className="text-xl font-semibold">Page Not Found</h2>
      <p className="text-sm text-muted-foreground">
        The page you&apos;re looking for doesn&apos;t exist.
      </p>
      <Link href="/dashboard" className={cn(buttonVariants())}>
        Go to Dashboard
      </Link>
    </div>
  );
}
