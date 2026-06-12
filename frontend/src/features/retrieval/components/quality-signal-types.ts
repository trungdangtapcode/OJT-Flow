export type BadgeVariant =
  | "default"
  | "success"
  | "warning"
  | "destructive"
  | "muted";

export type QualitySignalMetadataDetail = {
  label: string;
  values: string[];
  variant: "success" | "warning" | "destructive" | "muted";
};
