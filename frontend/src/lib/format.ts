import numeral from "numeral";
import { format, formatDistanceToNow, parseISO } from "date-fns";

export function formatCurrency(value: number, compact?: boolean): string {
  if (compact) {
    return "$" + numeral(value).format("0.[0]a").toUpperCase();
  }
  return numeral(value).format("$0,0.00");
}

export function formatPercent(value: number, decimals: number = 1): string {
  const fixed = value.toFixed(decimals);
  return `${fixed}%`;
}

export function formatNumber(value: number, compact?: boolean): string {
  if (compact) {
    return numeral(value).format("0.[0]a").toUpperCase();
  }
  return numeral(value).format("0,0");
}

export function formatDate(date: Date | string): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, "MMM d, yyyy");
}

export function formatRelativeDate(date: Date | string): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true });
}
