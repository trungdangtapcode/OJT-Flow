export type BadgeVariant = "default" | "success" | "warning" | "destructive" | "muted";

export type QueryDiagnosticListItem = {
  code: string;
  metadata: Record<string, unknown>;
  message: string;
  severity: string;
  suggestedAction: string;
};
