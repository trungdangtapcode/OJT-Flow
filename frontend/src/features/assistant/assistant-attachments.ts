import type { ExtractedDocument } from "../../types";
export {
  buildAssistantRetrievalContextHref,
  buildAssistantWorkflowContextHref,
} from "../../lib/assistant-context-links";
import { formatBytes } from "./assistant-format";

export type AssistantAttachmentSummary = {
  filename: string;
  source_format: string;
  extractor_used: string;
  char_count: number;
  warnings: string[];
  source: string | null;
  artifact_id: string | null;
  trace_id: string | null;
  job_id: string | null;
};

export type AssistantTextSnippet = {
  snippet_id: string;
  label: string;
  text: string;
  char_count: number;
  source: "manual";
};

export type AssistantSelectedContext = {
  context_id: string;
  source: "workflow" | "retrieval";
  label: string;
  summary: string;
  refs: Record<string, string | number | boolean | null>;
};

export type AssistantAttachmentSource = "upload" | "clipboard";

export type AssistantSelectedAttachment = {
  id: string;
  file: File;
  source: AssistantAttachmentSource;
};

export function parseContext(value: string):
  | { value: Record<string, unknown>; error?: never }
  | { value: Record<string, unknown>; error: string } {
  if (!value.trim()) return { value: {} };
  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return { value: parsed as Record<string, unknown> };
    }
    return { value: {}, error: "Context JSON must be an object." };
  } catch (error) {
    return {
      value: {},
      error: error instanceof Error ? error.message : "Context JSON is invalid.",
    };
  }
}

export function formatContext(context: Record<string, unknown>) {
  return Object.keys(context).length ? JSON.stringify(context, null, 2) : "";
}

export function assistantContextWithAttachments(
  context: Record<string, unknown>,
  documents: ExtractedDocument[],
  snippets: AssistantTextSnippet[] = [],
  selectedContexts: AssistantSelectedContext[] = [],
): Record<string, unknown> {
  if (!documents.length && !snippets.length && !selectedContexts.length) return context;
  const attachments = documents.map(documentAttachment);
  const existingSelectedContexts = selectedContextsFromContext(context);
  const existingTextSnippets = textSnippetsFromContext(context);
  const nextSelectedContexts = [
    ...existingSelectedContexts,
    ...selectedContexts.filter(
      (candidate) =>
        !existingSelectedContexts.some(
          (existing) => existing.context_id === candidate.context_id,
        ),
    ),
  ];
  const nextTextSnippets = [
    ...existingTextSnippets,
    ...snippets.filter(
      (candidate) =>
        !existingTextSnippets.some(
          (existing) => existing.snippet_id === candidate.snippet_id,
        ),
    ),
  ];
  const generatedData = combinedContextData({
    attachments,
    snippets: nextTextSnippets,
  });
  return {
    ...context,
    data:
      typeof context.data === "string" && context.data.trim()
        ? context.data
        : generatedData || undefined,
    input_format:
      typeof context.input_format === "string" && context.input_format.trim()
        ? context.input_format
        : inferredInputFormat(documents, nextTextSnippets),
    attachments: [
      ...attachmentSummariesFromContext(context),
      ...attachments,
    ],
    text_snippets: nextTextSnippets,
    selected_contexts: nextSelectedContexts,
  };
}

export function assistantContextWithAttachment(
  context: Record<string, unknown>,
  document: ExtractedDocument | null,
): Record<string, unknown> {
  return assistantContextWithAttachments(context, document ? [document] : []);
}

export function attachmentSummariesFromContext(
  context: Record<string, unknown>,
): AssistantAttachmentSummary[] {
  const attachments = context.attachments;
  if (!Array.isArray(attachments)) return [];
  return attachments
    .map((item) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return null;
      const record = item as Record<string, unknown>;
      const filename = typeof record.filename === "string" ? record.filename : "";
      const sourceFormat =
        typeof record.source_format === "string" ? record.source_format : "unknown";
      const extractorUsed =
        typeof record.extractor_used === "string" ? record.extractor_used : "unknown";
      const charCount =
        typeof record.char_count === "number" && Number.isFinite(record.char_count)
          ? record.char_count
          : 0;
      const warnings = Array.isArray(record.warnings)
        ? record.warnings.filter((warning): warning is string => typeof warning === "string")
        : [];
      const source = typeof record.source === "string" ? record.source : null;
      const artifactId =
        typeof record.artifact_id === "string" ? record.artifact_id : null;
      const traceId = typeof record.trace_id === "string" ? record.trace_id : null;
      const jobId = typeof record.job_id === "string" ? record.job_id : null;
      return filename
        ? {
            filename,
            source_format: sourceFormat,
            extractor_used: extractorUsed,
            char_count: charCount,
            warnings,
            source,
            artifact_id: artifactId,
            trace_id: traceId,
            job_id: jobId,
          }
        : null;
    })
    .filter((item): item is AssistantAttachmentSummary => item !== null);
}

export function textSnippetsFromContext(
  context: Record<string, unknown>,
): AssistantTextSnippet[] {
  const snippets = context.text_snippets;
  if (!Array.isArray(snippets)) return [];
  return snippets
    .map((item) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return null;
      const record = item as Record<string, unknown>;
      const text = typeof record.text === "string" ? record.text : "";
      const label = typeof record.label === "string" ? record.label : "Text snippet";
      const snippetId =
        typeof record.snippet_id === "string"
          ? record.snippet_id
          : `snippet_${hashText(`${label}:${text}`).slice(0, 10)}`;
      if (!text.trim()) return null;
      return {
        snippet_id: snippetId,
        label,
        text,
        char_count:
          typeof record.char_count === "number" && Number.isFinite(record.char_count)
            ? record.char_count
            : text.length,
        source: "manual" as const,
      };
    })
    .filter((item): item is AssistantTextSnippet => item !== null);
}

export function selectedContextsFromContext(
  context: Record<string, unknown>,
): AssistantSelectedContext[] {
  const selected = context.selected_contexts;
  if (!Array.isArray(selected)) return [];
  return selected
    .map((item) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return null;
      const record = item as Record<string, unknown>;
      const source = record.source === "workflow" || record.source === "retrieval"
        ? record.source
        : null;
      const label = typeof record.label === "string" ? record.label : "";
      const summary = typeof record.summary === "string" ? record.summary : "";
      const contextId =
        typeof record.context_id === "string" ? record.context_id : `${source}:${label}`;
      const refs = record.refs && typeof record.refs === "object" && !Array.isArray(record.refs)
        ? compactRefs(record.refs as Record<string, unknown>)
        : {};
      return source && label
        ? {
            context_id: contextId,
            source,
            label,
            summary,
            refs,
          }
        : null;
    })
    .filter((item): item is AssistantSelectedContext => item !== null);
}

export function validateAssistantAttachment(
  file: File,
  allowedExtensions: string[],
  maxUploadBytes: number | null,
): string | null {
  if (maxUploadBytes && file.size > maxUploadBytes) {
    return `Attachment is too large: ${formatBytes(file.size)} selected, ${formatBytes(
      maxUploadBytes,
    )} allowed.`;
  }
  const allowed = new Set(
    allowedExtensions
      .map((extension) => extension.trim().toLowerCase())
      .filter(Boolean),
  );
  if (!allowed.size) return null;
  const extension = extensionFromFilename(file.name);
  if (!extension) {
    return "Attachment needs a supported file extension.";
  }
  if (!allowed.has(extension)) {
    return `Unsupported attachment type ${extension}. Supported: ${allowedExtensions.join(", ")}.`;
  }
  return null;
}

export function validateAssistantAttachments(
  files: File[],
  allowedExtensions: string[],
  maxUploadBytes: number | null,
): string | null {
  for (const file of files) {
    const error = validateAssistantAttachment(file, allowedExtensions, maxUploadBytes);
    if (error) return `${file.name || "Attachment"}: ${error}`;
  }
  return null;
}

export function filesFromClipboard(clipboardData: DataTransfer): File[] {
  const files = Array.from(clipboardData.files).filter((file) =>
    Boolean(file.name || file.type),
  );
  if (files.length) return files;
  for (const item of Array.from(clipboardData.items)) {
    if (item.kind !== "file") continue;
    const file = item.getAsFile();
    if (!file) continue;
    if (file.name) return [file];
    const extension = extensionFromMimeType(file.type);
    return [
      new File([file], `clipboard-image-${Date.now()}${extension}`, {
        type: file.type,
      }),
    ];
  }
  return [];
}

export function fileFromClipboard(clipboardData: DataTransfer): File | null {
  return filesFromClipboard(clipboardData)[0] ?? null;
}

export function assistantContextFromSearchParams(
  searchParams: URLSearchParams,
): {
  context: Record<string, unknown>;
  message: string;
} | null {
  const selectedContexts: AssistantSelectedContext[] = [];
  const workflowId = searchParams.get("workflow_id")?.trim();
  if (workflowId) {
    selectedContexts.push({
      context_id: `workflow:${workflowId}`,
      source: "workflow",
      label: workflowId,
      summary: "Selected workflow context from the workflow detail page.",
      refs: { workflow_id: workflowId },
    });
  }
  const retrievalQuery = searchParams.get("retrieval_query")?.trim();
  if (retrievalQuery) {
    const strategy = searchParams.get("retrieval_strategy")?.trim() || null;
    const runId = searchParams.get("retrieval_run_id")?.trim() || null;
    selectedContexts.push({
      context_id: `retrieval:${hashText(`${retrievalQuery}:${strategy ?? ""}`)}`,
      source: "retrieval",
      label: retrievalQuery,
      summary: "Selected retrieval run context from the Retrieval page.",
      refs: {
        retrieval_query: retrievalQuery,
        retrieval_strategy: strategy,
        retrieval_run_id: runId,
      },
    });
  }
  if (!selectedContexts.length) return null;
  const context = assistantContextWithAttachments({}, [], [], selectedContexts);
  const message =
    selectedContexts[0]?.source === "workflow"
      ? "Inspect this selected workflow context and explain what needs attention."
      : "Use this selected retrieval context to explain evidence quality and next steps.";
  return { context, message };
}

export async function fileToBase64(file: File): Promise<string> {
  const buffer = await file.arrayBuffer();
  let binary = "";
  const bytes = new Uint8Array(buffer);
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    const chunk = bytes.subarray(index, index + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
}

function extensionFromMimeType(mimeType: string) {
  if (mimeType === "image/png") return ".png";
  if (mimeType === "image/jpeg") return ".jpg";
  if (mimeType === "image/webp") return ".webp";
  if (mimeType === "image/gif") return ".gif";
  if (mimeType === "image/tiff") return ".tiff";
  return "";
}

function extensionFromFilename(filename: string) {
  const dotIndex = filename.lastIndexOf(".");
  if (dotIndex < 0) return "";
  return filename.slice(dotIndex).toLowerCase();
}

function documentAttachment(document: ExtractedDocument) {
  const text = typeof document.text === "string" ? document.text : "";
  return {
    filename: document.filename,
    source_format: document.source_format,
    extractor_used: document.extractor_used,
    page_count: document.page_count ?? null,
    char_count: document.char_count,
    word_count: document.word_count,
    warnings: document.warnings,
    source: document.source ?? null,
    artifact_id: document.artifact_id ?? null,
    trace_id: document.trace_id ?? null,
    job_id: document.job_id ?? null,
    text_dataset_id: document.text_dataset_id ?? null,
    text_storage_ref: document.text_storage_ref ?? null,
    text,
  };
}

function combinedContextData({
  attachments,
  snippets,
}: {
  attachments: Array<ReturnType<typeof documentAttachment>>;
  snippets: AssistantTextSnippet[];
}) {
  const sections = [
    ...snippets.map(
      (snippet) =>
        `BEGIN TEXT SNIPPET ${snippet.label}\n${snippet.text}\nEND TEXT SNIPPET ${snippet.label}`,
    ),
    ...attachments
      .filter((attachment) => attachment.text.trim())
      .map(
      (attachment) =>
        `BEGIN ATTACHMENT ${attachment.filename} (${attachment.source_format})\n${attachment.text}\nEND ATTACHMENT ${attachment.filename}`,
      ),
  ];
  return sections.join("\n\n");
}

function inferredInputFormat(
  documents: ExtractedDocument[],
  snippets: AssistantTextSnippet[],
) {
  if (documents.length === 1 && snippets.length === 0) {
    return assistantParserFormatForDocument(documents[0].source_format);
  }
  if (!documents.length && snippets.length === 1) return "markdown";
  return documents.length || snippets.length ? "markdown" : undefined;
}

function assistantParserFormatForDocument(sourceFormat: string) {
  const normalized = sourceFormat.trim().toLowerCase().replaceAll("-", "_");
  if (["json", "yaml", "csv", "ndjson", "markdown"].includes(normalized)) {
    return normalized;
  }
  return "markdown";
}

function compactRefs(record: Record<string, unknown>) {
  return Object.fromEntries(
    Object.entries(record).filter(
      (entry): entry is [string, string | number | boolean | null] => {
        const value = entry[1];
        return (
          value === null ||
          typeof value === "string" ||
          typeof value === "number" ||
          typeof value === "boolean"
        );
      },
    ),
  );
}

function hashText(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}
