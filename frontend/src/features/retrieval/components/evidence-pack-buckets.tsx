import { Badge } from "../../../components/ui/badge";
import { humanize } from "../../../lib/utils";
import type { RetrievalEvidenceBucket } from "../../../types";

export function EvidencePackBuckets({ buckets }: { buckets: RetrievalEvidenceBucket[] }) {
  if (!buckets.length) return null;
  const availableCount = buckets.filter((bucket) => bucket.hit_count > 0).length;
  const missingRequiredCount = buckets.filter(
    (bucket) => bucket.required && bucket.hit_count === 0,
  ).length;
  return (
    <div className="grid gap-2 rounded-lg border border-border/60 bg-muted/20 p-3">
      <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
        <div>
          <div className="text-xs font-bold uppercase text-muted-foreground">
            Evidence pack
          </div>
          <div className="mt-1 text-sm font-semibold">
            {formatCount(availableCount, "bucket")} with selected evidence
          </div>
        </div>
        <Badge variant={missingRequiredCount ? "warning" : "success"}>
          {missingRequiredCount
            ? formatCount(missingRequiredCount, "required gap")
            : "complete"}
        </Badge>
      </div>
      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
        {buckets.map((bucket) => (
          <div
            className="grid min-w-0 gap-1 rounded-lg border border-border/60 bg-card px-3 py-2 text-xs"
            key={bucket.bucket_id}
          >
            <div className="flex min-w-0 flex-wrap items-center justify-between gap-2">
              <span className="break-words font-bold">{bucket.label}</span>
              <Badge variant={evidenceBucketBadgeVariant(bucket)}>
                {formatCount(bucket.hit_count, "hit")}
              </Badge>
            </div>
            <div className="break-words text-muted-foreground">
              {bucket.description}
            </div>
            <div className="flex min-w-0 flex-wrap gap-1.5">
              {bucket.required ? <Badge variant="muted">required</Badge> : null}
              {bucket.source_ids.slice(0, 3).map((sourceId) => (
                <Badge className="max-w-full break-words" key={sourceId} variant="muted">
                  {sourceId}
                </Badge>
              ))}
              {bucket.source_ids.length > 3 ? (
                <Badge variant="muted">+{bucket.source_ids.length - 3}</Badge>
              ) : null}
              {bucket.warnings.map((warning) => (
                <Badge className="max-w-full break-words" key={warning} variant="warning">
                  {humanize(warning)}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function evidenceBucketBadgeVariant(
  bucket: RetrievalEvidenceBucket,
): "success" | "warning" | "muted" {
  if (bucket.hit_count > 0) return "success";
  return bucket.required ? "warning" : "muted";
}

function formatCount(count: number, singular: string) {
  return `${count} ${singular}${count === 1 ? "" : "s"}`;
}
