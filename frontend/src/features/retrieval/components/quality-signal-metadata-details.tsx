import { Badge } from "../../../components/ui/badge";
import type { RetrievalQualitySignal } from "../../../types";
import { qualitySignalMetadataDetails } from "./quality-signal-metadata";

export function QualitySignalMetadataDetails({
  signal,
}: {
  signal: RetrievalQualitySignal;
}) {
  const details = qualitySignalMetadataDetails(signal);
  if (!details.length) return null;
  return (
    <div className="grid gap-1.5 rounded-md border border-border bg-muted/20 p-2">
      <div className="text-[11px] font-bold uppercase text-muted-foreground">
        Signal details
      </div>
      <div className="grid gap-1.5">
        {details.map((detail) => (
          <div className="grid gap-1" key={detail.label}>
            <span className="font-bold text-muted-foreground">{detail.label}</span>
            <div className="flex min-w-0 flex-wrap gap-1">
              {detail.values.map((value) => (
                <Badge
                  className="max-w-full break-words text-left"
                  key={`${detail.label}-${value}`}
                  variant={detail.variant}
                >
                  {value}
                </Badge>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
