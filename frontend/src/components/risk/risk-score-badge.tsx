"use client";

import { cn } from "@/lib/utils";

interface RiskScoreBadgeProps {
  score: number | null;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
}

function getRiskLevel(score: number): {
  label: string;
  color: string;
  bg: string;
} {
  if (score >= 70)
    return {
      label: "Critical",
      color: "text-red-700 dark:text-red-400",
      bg: "bg-red-100 dark:bg-red-950",
    };
  if (score >= 50)
    return {
      label: "High",
      color: "text-orange-700 dark:text-orange-400",
      bg: "bg-orange-100 dark:bg-orange-950",
    };
  if (score >= 30)
    return {
      label: "Medium",
      color: "text-yellow-700 dark:text-yellow-400",
      bg: "bg-yellow-100 dark:bg-yellow-950",
    };
  return {
    label: "Low",
    color: "text-green-700 dark:text-green-400",
    bg: "bg-green-100 dark:bg-green-950",
  };
}

export function RiskScoreBadge({
  score,
  size = "md",
  showLabel = true,
}: RiskScoreBadgeProps) {
  if (score === null || score === undefined) {
    return (
      <span className="text-xs text-muted-foreground">No score</span>
    );
  }

  const { label, color, bg } = getRiskLevel(score);

  const sizeClasses = {
    sm: "text-xs px-1.5 py-0.5",
    md: "text-sm px-2 py-0.5",
    lg: "text-base px-3 py-1",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full font-medium",
        sizeClasses[size],
        color,
        bg
      )}
    >
      <span className="font-bold">{score}</span>
      {showLabel && <span className="font-normal">/ 100 {label}</span>}
    </span>
  );
}
