export function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

export function humanizeWorkbenchValue(value: string) {
  return value.replaceAll("_", " ");
}

export function sourceDataStats(value: string) {
  const normalized = value.trimEnd();
  return {
    bytes: new TextEncoder().encode(value).length,
    lines: normalized ? normalized.split(/\r?\n/).length : 0,
  };
}

export function validateUploadFile(
  file: File,
  allowedExtensions: string[],
  maxUploadBytes: number | null,
) {
  if (maxUploadBytes && file.size > maxUploadBytes) {
    return `File exceeds upload limit (${formatBytes(file.size)} selected / ${formatBytes(maxUploadBytes)} max).`;
  }

  if (!allowedExtensions.length) return null;

  const extension = fileExtension(file.name);
  const normalizedAllowed = new Set(
    allowedExtensions.map((value) => value.trim().toLowerCase()).filter(Boolean),
  );
  if (!extension || !normalizedAllowed.has(extension)) {
    return `Unsupported file type${extension ? ` ${extension}` : ""}. Accepted: ${formatExtensionSummary(allowedExtensions)}.`;
  }

  return null;
}

function fileExtension(fileName: string) {
  const lastSegment = fileName.split(/[\\/]/).pop() ?? "";
  const dotIndex = lastSegment.lastIndexOf(".");
  if (dotIndex <= 0 || dotIndex === lastSegment.length - 1) return null;
  return lastSegment.slice(dotIndex).toLowerCase();
}

function formatExtensionSummary(extensions: string[]) {
  const normalized = extensions.map((extension) => extension.trim()).filter(Boolean);
  const visible = normalized.slice(0, 8).join(", ");
  const remaining = normalized.length - 8;
  return remaining > 0 ? `${visible}, +${remaining} more` : visible;
}
