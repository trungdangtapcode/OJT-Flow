export function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatCount(value: number, noun: string) {
  return `${value} ${noun}${value === 1 ? "" : "s"}`;
}

export function previewJson(value: Record<string, unknown>) {
  const json = JSON.stringify(value, null, 2);
  return json.length > 5000 ? `${json.slice(0, 5000)}\n...` : json;
}
