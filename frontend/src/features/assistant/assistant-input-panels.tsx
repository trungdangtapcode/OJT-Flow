import { Image, Paperclip, Settings2, X } from "lucide-react";

import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Label, Textarea } from "../../components/ui/form";
import { HelpTooltip } from "../../components/ui/help-tooltip";
import type {
  AssistantMemoryPolicy,
  AssistantMemorySnapshot,
  AssistantMemoryValue,
  AssistantToolSpec,
} from "../../types";
import { formatBytes, formatCount } from "./assistant-format";

export function AttachmentPreview({
  file,
  onRemove,
  source = "upload",
}: {
  file: File;
  onRemove: () => void;
  source?: "upload" | "clipboard";
}) {
  const isImage = file.type.startsWith("image/");
  return (
    <div className="flex min-w-0 flex-wrap items-center justify-between gap-2 rounded-md border border-border bg-muted/30 px-3 py-2 text-sm">
      <div className="flex min-w-0 items-center gap-2">
        {isImage ? (
          <Image className="h-4 w-4 shrink-0 text-primary" />
        ) : (
          <Paperclip className="h-4 w-4 shrink-0 text-primary" />
        )}
        <div className="min-w-0">
          <div className="truncate font-black">{file.name}</div>
          <div className="text-xs text-muted-foreground">
            {file.type || "unknown type"} / {formatBytes(file.size)}
          </div>
        </div>
      </div>
      <Badge variant={source === "clipboard" ? "success" : "muted"}>
        {source === "clipboard" ? "pasted image" : "attached file"}
      </Badge>
      <Button
        aria-label="Remove attached file"
        onClick={onRemove}
        size="sm"
        type="button"
        variant="ghost"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function AttachmentCapabilityBadge({
  availableExtractors,
  isLoading,
  supportedExtensions,
}: {
  availableExtractors: string[];
  isLoading: boolean;
  supportedExtensions: string[];
}) {
  const primaryExtractor = availableExtractors[0] ?? null;
  const hasVisionOcr = availableExtractors.includes("openai_vision");
  const imageCapable = supportedExtensions.some((extension) =>
    [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif"].includes(extension.toLowerCase()),
  );
  return (
    <span className="flex min-w-0 flex-wrap items-center gap-1.5 text-xs font-semibold text-muted-foreground">
      <Badge variant={availableExtractors.length ? "success" : "warning"}>
        {isLoading
          ? "checking extractors"
          : hasVisionOcr
            ? "vision OCR enabled"
            : primaryExtractor
              ? `${primaryExtractor} parser`
              : "parser unavailable"}
      </Badge>
      {imageCapable ? <Badge variant="muted">image paste</Badge> : null}
      {supportedExtensions.length ? (
        <Badge variant="muted">{formatCount(supportedExtensions.length, "format")}</Badge>
      ) : null}
    </span>
  );
}

export function AssistantControlsPanel({
  contextText,
  executeWriteActions,
  isMemoryUpdating,
  memoryMutationKey,
  memoryPolicy,
  memorySnapshot,
  onContextTextChange,
  onExecuteWriteActionsChange,
  onMemoryPreferenceChange,
  onMemoryPreferenceDelete,
  onWriteConfirmationAcceptedChange,
  writeConfirmationAccepted,
  writeGatedTools,
}: {
  contextText: string;
  executeWriteActions: boolean;
  isMemoryUpdating: boolean;
  memoryMutationKey: string | null;
  memoryPolicy?: AssistantMemoryPolicy;
  memorySnapshot?: AssistantMemorySnapshot;
  onContextTextChange: (value: string) => void;
  onExecuteWriteActionsChange: (value: boolean) => void;
  onMemoryPreferenceChange: (key: string, value: AssistantMemoryValue) => void;
  onMemoryPreferenceDelete: (key: string) => void;
  onWriteConfirmationAcceptedChange: (value: boolean) => void;
  writeConfirmationAccepted: boolean;
  writeGatedTools: AssistantToolSpec[];
}) {
  return (
    <details className="group relative">
      <summary className="flex h-10 cursor-pointer list-none items-center gap-2 rounded-md border border-border bg-card px-3 text-sm font-black shadow-sm transition hover:border-primary">
        <Settings2 className="h-4 w-4 text-primary" />
        Advanced context
      </summary>
      <div className="absolute bottom-12 right-0 z-20 hidden w-[min(620px,calc(100vw-2rem))] gap-4 rounded-md border border-border bg-card p-4 shadow-lg group-open:grid">
        <div>
          <div className="text-sm font-black">Advanced context</div>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Context and safety gates for the next message.
          </p>
        </div>
        <label className="flex items-center gap-2 rounded-md border border-border bg-muted/35 px-3 py-2 text-sm font-semibold">
          <input
            checked={executeWriteActions}
            className="h-4 w-4 accent-primary"
            onChange={(event) => {
              onExecuteWriteActionsChange(event.target.checked);
              if (!event.target.checked) {
                onWriteConfirmationAcceptedChange(false);
              }
            }}
            type="checkbox"
          />
          Execute write actions
          <HelpTooltip label="Execute write actions help">
            Keep this off for normal questions. Turn it on only when you explicitly want the assistant to run approved write-capable tools.
          </HelpTooltip>
        </label>
        {executeWriteActions ? (
          <div className="grid gap-3 rounded-md border border-amber-200 bg-amber-50 px-3 py-3 text-sm text-amber-950">
            <div>
              <div className="font-black">Write action confirmation</div>
              <p className="mt-1 leading-6">
                Confirm before the assistant may run write-gated tools. The
                backend still enforces each tool permission gate.
              </p>
            </div>
            <div className="grid gap-2">
              {writeGatedTools.length ? (
                writeGatedTools.map((tool) => (
                  <div
                    className="rounded-md border border-amber-200 bg-card px-3 py-2"
                    key={tool.name}
                  >
                    <div className="flex min-w-0 flex-wrap items-center gap-2">
                      <span className="break-words font-mono text-xs font-black">
                        {tool.name}
                      </span>
                      <Badge variant="warning">{tool.risk_level}</Badge>
                      <Badge variant="muted">{tool.permission_scope}</Badge>
                    </div>
                    {tool.approval_reason ? (
                      <div className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">
                        {tool.approval_reason}
                      </div>
                    ) : null}
                  </div>
                ))
              ) : (
                <div className="rounded-md border border-amber-200 bg-card px-3 py-2 text-xs font-semibold text-muted-foreground">
                  No write-gated Assistant tools are advertised by the current backend catalog.
                </div>
              )}
            </div>
            <label className="flex items-start gap-2 rounded-md border border-amber-200 bg-card px-3 py-2 text-xs font-bold">
              <input
                checked={writeConfirmationAccepted}
                className="mt-0.5 h-4 w-4 accent-primary"
                onChange={(event) =>
                  onWriteConfirmationAcceptedChange(event.target.checked)
                }
                type="checkbox"
              />
              <span>
                I confirm this next assistant command may execute write-gated
                backend tools if the validated plan selects them.
              </span>
            </label>
          </div>
        ) : null}
        <AssistantMemoryPanel
          isUpdating={isMemoryUpdating}
          mutationKey={memoryMutationKey}
          onPreferenceChange={onMemoryPreferenceChange}
          onPreferenceDelete={onMemoryPreferenceDelete}
          policy={memoryPolicy}
          snapshot={memorySnapshot}
        />
        <Label>
          <span className="inline-flex items-center gap-1.5">
            Optional context JSON
            <HelpTooltip label="Optional context JSON help">
              Structured data for the next message. Use this for schema IDs, formats, fields, or payload snippets when the chat text alone is not enough.
            </HelpTooltip>
          </span>
          <Textarea
            className="min-h-48 resize-y font-mono text-xs"
            onChange={(event) => onContextTextChange(event.target.value)}
            spellCheck={false}
            value={contextText}
          />
        </Label>
      </div>
    </details>
  );
}

function AssistantMemoryPanel({
  isUpdating,
  mutationKey,
  onPreferenceChange,
  onPreferenceDelete,
  policy,
  snapshot,
}: {
  isUpdating: boolean;
  mutationKey: string | null;
  onPreferenceChange: (key: string, value: AssistantMemoryValue) => void;
  onPreferenceDelete: (key: string) => void;
  policy?: AssistantMemoryPolicy;
  snapshot?: AssistantMemorySnapshot;
}) {
  const savedValues = new Map(
    (snapshot?.preferences ?? []).map((preference) => [preference.key, preference.value]),
  );
  const definitions = policy?.preferences ?? [];
  return (
    <section className="grid gap-3 rounded-md border border-border bg-muted/25 px-3 py-3">
      <div>
        <div className="flex min-w-0 flex-wrap items-center gap-2 text-sm font-black">
          Assistant memory
          <Badge variant="muted">preferences only</Badge>
        </div>
        <p className="mt-1 text-xs font-semibold leading-5 text-muted-foreground">
          Stored memory is limited to backend-approved operational preferences. Raw data,
          uploaded content, patient identifiers, and clinical facts are rejected.
        </p>
      </div>
      {definitions.length ? (
        <div className="grid gap-2">
          {definitions.map((definition) => {
            const hasSavedValue = savedValues.has(definition.key);
            const value = savedValues.get(definition.key) ?? definition.default_value ?? "";
            const updating = isUpdating && mutationKey === definition.key;
            return (
              <div
                className="grid gap-2 rounded-md border border-border bg-card px-3 py-2"
                key={definition.key}
              >
                <div className="flex min-w-0 flex-wrap items-start justify-between gap-2">
                  <div className="min-w-0">
                    <div className="break-words text-sm font-black">
                      {definition.label}
                    </div>
                    <div className="mt-0.5 text-xs font-semibold leading-5 text-muted-foreground">
                      {definition.description}
                    </div>
                  </div>
                  <div className="flex shrink-0 flex-wrap items-center gap-1">
                    <Badge variant={hasSavedValue ? "success" : "muted"}>
                      {hasSavedValue ? "saved" : "default"}
                    </Badge>
                    <Badge variant="muted">{definition.category}</Badge>
                  </div>
                </div>
                <div className="flex min-w-0 flex-wrap items-center gap-2">
                  <MemoryInput
                    definition={definition}
                    disabled={updating}
                    onChange={(nextValue) =>
                      onPreferenceChange(definition.key, nextValue)
                    }
                    value={value}
                  />
                  {hasSavedValue ? (
                    <Button
                      disabled={updating}
                      onClick={() => onPreferenceDelete(definition.key)}
                      size="sm"
                      type="button"
                      variant="ghost"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  ) : null}
                  {updating ? (
                    <span className="text-xs font-semibold text-muted-foreground">
                      saving
                    </span>
                  ) : null}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="rounded-md border border-border bg-card px-3 py-2 text-xs font-semibold text-muted-foreground">
          Assistant memory policy is unavailable from the backend.
        </div>
      )}
    </section>
  );
}

function MemoryInput({
  definition,
  disabled,
  onChange,
  value,
}: {
  definition: AssistantMemoryPolicy["preferences"][number];
  disabled: boolean;
  onChange: (value: AssistantMemoryValue) => void;
  value: AssistantMemoryValue | "";
}) {
  if (definition.value_type === "boolean") {
    return (
      <label className="inline-flex min-h-9 items-center gap-2 rounded-md border border-border bg-background px-3 text-sm font-semibold">
        <input
          checked={Boolean(value)}
          className="h-4 w-4 accent-primary"
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
          type="checkbox"
        />
        enabled
      </label>
    );
  }
  if (definition.value_type === "enum") {
    return (
      <select
        className="h-9 min-w-48 rounded-md border border-border bg-background px-3 text-sm font-semibold"
        disabled={disabled}
        onChange={(event) => onChange(event.target.value)}
        value={String(value)}
      >
        {definition.allowed_values.map((option) => (
          <option key={String(option)} value={String(option)}>
            {String(option).replaceAll("_", " ")}
          </option>
        ))}
      </select>
    );
  }
  if (definition.value_type === "number") {
    return (
      <input
        className="h-9 min-w-32 rounded-md border border-border bg-background px-3 text-sm font-semibold"
        disabled={disabled}
        maxLength={definition.max_length}
        onChange={(event) => onChange(Number(event.target.value))}
        type="number"
        value={String(value)}
      />
    );
  }
  return (
    <input
      className="h-9 min-w-48 rounded-md border border-border bg-background px-3 text-sm font-semibold"
      disabled={disabled}
      maxLength={definition.max_length}
      onChange={(event) => onChange(event.target.value)}
      type="text"
      value={String(value)}
    />
  );
}
