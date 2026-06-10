import type { ExtractedDocument } from "../../types";
import { formatBytes } from "./assistant-format";

export type AssistantAttachmentSummary = {
  filename: string;
  source_format: string;
  extractor_used: string;
  char_count: number;
  warnings: string[];
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

export function assistantContextWithAttachment(
  context: Record<string, unknown>,
  document: ExtractedDocument | null,
): Record<string, unknown> {
  if (!document) return context;
  const attachment = {
    filename: document.filename,
    source_format: document.source_format,
    extractor_used: document.extractor_used,
    page_count: document.page_count ?? null,
    char_count: document.char_count,
    word_count: document.word_count,
    warnings: document.warnings,
  };
  return {
    ...context,
    data:
      typeof context.data === "string" && context.data.trim()
        ? context.data
        : document.text,
    input_format:
      typeof context.input_format === "string" && context.input_format.trim()
        ? context.input_format
        : document.source_format,
    attachments: [
      ...attachmentSummariesFromContext(context),
      {
        ...attachment,
        text: document.text,
      },
    ],
  };
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
      return filename
        ? {
            filename,
            source_format: sourceFormat,
            extractor_used: extractorUsed,
            char_count: charCount,
            warnings,
          }
        : null;
    })
    .filter((item): item is AssistantAttachmentSummary => item !== null);
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

export function fileFromClipboard(clipboardData: DataTransfer): File | null {
  const fileFromList = Array.from(clipboardData.files).find((file) =>
    Boolean(file.name || file.type),
  );
  if (fileFromList) return fileFromList;
  for (const item of Array.from(clipboardData.items)) {
    if (item.kind !== "file") continue;
    const file = item.getAsFile();
    if (!file) continue;
    if (file.name) return file;
    const extension = extensionFromMimeType(file.type);
    return new File([file], `clipboard-image-${Date.now()}${extension}`, {
      type: file.type,
    });
  }
  return null;
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
