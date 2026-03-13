import type { ProbabilityPoint } from "@/types";
import type { ChildHistory } from "@/hooks/use-events";

/**
 * Extract a numeric value from an outcome label.
 * Handles: "Above 10", "10 or more", "10-15" (midpoint), "15.5", "$10M"
 * Returns null for non-numeric labels like "Claude", "Biden", "Yes/No".
 */
export function extractNumericValue(label: string): number | null {
  const s = label.trim();

  // "Above X", "Over X", "More than X", "At least X", ">X", ">=X"
  let m = s.match(/(?:above|over|more than|at least|>=?)\s*\$?([\d,]+\.?\d*)/i);
  if (m) return parseFloat(m[1].replace(/,/g, ""));

  // "X or more", "X+"
  m = s.match(/([\d,]+\.?\d*)\s*(?:or more|\+)/i);
  if (m) return parseFloat(m[1].replace(/,/g, ""));

  // "Below X", "Under X", "Less than X", "<X", "<=X"
  m = s.match(/(?:below|under|less than|at most|<=?)\s*\$?([\d,]+\.?\d*)/i);
  if (m) return parseFloat(m[1].replace(/,/g, ""));

  // "X or fewer", "X or less"
  m = s.match(/([\d,]+\.?\d*)\s*(?:or fewer|or less)/i);
  if (m) return parseFloat(m[1].replace(/,/g, ""));

  // Range: "10-15", "10–15" → midpoint
  m = s.match(/\$?([\d,]+\.?\d*)\s*[-–—]\s*\$?([\d,]+\.?\d*)/);
  if (m) {
    const lo = parseFloat(m[1].replace(/,/g, ""));
    const hi = parseFloat(m[2].replace(/,/g, ""));
    return (lo + hi) / 2;
  }

  // "X to Y" → midpoint
  m = s.match(/([\d,]+\.?\d*)\s+to\s+([\d,]+\.?\d*)/i);
  if (m) {
    const lo = parseFloat(m[1].replace(/,/g, ""));
    const hi = parseFloat(m[2].replace(/,/g, ""));
    return (lo + hi) / 2;
  }

  // Bare number: "15", "$10", "15.5"
  m = s.match(/^\$?([\d,]+\.?\d*)\s*[%MBKmbk]?$/);
  if (m) return parseFloat(m[1].replace(/,/g, ""));

  return null;
}

export interface EVPoint {
  date: string;
  ev: number;
}

/**
 * Compute EV timeseries from children history.
 * At each timestamp: EV = sum(p_i * v_i) / sum(p_i)
 * where v_i is the numeric value extracted from the child's title.
 */
export function computeEVTimeseries(
  childrenHistory: Record<string, ChildHistory>,
  children: { id: string; title: string }[],
): EVPoint[] {
  // Map child IDs to their numeric values
  const childValues: Record<string, number> = {};
  for (const child of children) {
    const v = extractNumericValue(child.title);
    if (v !== null) {
      childValues[child.id] = v;
    }
  }

  if (Object.keys(childValues).length === 0) return [];

  // Collect all timestamps across all children with numeric values
  const dateMap = new Map<string, { numerator: number; denominator: number }>();

  for (const [childId, data] of Object.entries(childrenHistory)) {
    const value = childValues[childId];
    if (value === undefined) continue;

    for (const point of data.history) {
      const key = point.date;
      if (!dateMap.has(key)) {
        dateMap.set(key, { numerator: 0, denominator: 0 });
      }
      const entry = dateMap.get(key)!;
      entry.numerator += point.probability * value;
      entry.denominator += point.probability;
    }
  }

  // Sort by date and compute EV
  return Array.from(dateMap.entries())
    .sort(([a], [b]) => new Date(a).getTime() - new Date(b).getTime())
    .filter(([, { denominator }]) => denominator > 0)
    .map(([date, { numerator, denominator }]) => ({
      date,
      ev: numerator / denominator,
    }));
}
