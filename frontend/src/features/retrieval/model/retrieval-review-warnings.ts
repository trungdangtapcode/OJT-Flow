import type { RetrievalPackage } from "../../../types";

export function retrievalPackageWarnings(packageData: RetrievalPackage): string[] {
  return [
    ...(packageData.trace.warnings ?? []),
    ...((packageData.coverage?.warnings ?? []) as string[]),
  ].filter((warning) => warning.trim());
}

export function formatReviewCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
