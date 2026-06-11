export function formatClaim(claim: string): string {
  return claim
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/[ \t]+/g, " ")
    .trim();
}

export function formatConfidence(confidence: number | null | undefined): string {
  return typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : "n/a";
}

export function formatScore(score: number): string {
  return score.toFixed(3);
}

export function formatCount(
  count: number,
  singular: string,
  plural = `${singular}s`,
): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

export function formatPercent(value: number): string {
  if (!Number.isFinite(value)) return "n/a";
  return `${Math.round(value * 100)}%`;
}

export function formatDecimal(value: number): string {
  if (!Number.isFinite(value)) return "n/a";
  return value.toFixed(1);
}

export function formatNullablePercent(value: number | null): string {
  return value === null ? "n/a" : formatPercent(value);
}

export function formatNullableDecimal(value: number | null): string {
  return value === null ? "n/a" : formatDecimal(value);
}

export function formatShortSignature(signature: string): string {
  const digest = signature.includes(":") ? signature.split(":").pop() ?? signature : signature;
  return `sig ${digest.slice(0, 10)}`;
}
