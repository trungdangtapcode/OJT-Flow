export function correctiveActionTypeCountEntries(
  counts: Record<string, number>,
): Array<[string, number]> {
  return Object.entries(counts)
    .filter(([, count]) => Number.isFinite(count) && count > 0)
    .sort(([leftType, leftCount], [rightType, rightCount]) => {
      if (rightCount !== leftCount) return rightCount - leftCount;
      return leftType.localeCompare(rightType);
    });
}
