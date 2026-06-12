import * as React from "react";

export async function copyTextToClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  textarea.style.left = "-9999px";
  document.body.appendChild(textarea);
  textarea.select();
  try {
    document.execCommand("copy");
  } finally {
    document.body.removeChild(textarea);
  }
}

export function useCopyFeedback(timeoutMs = 1800) {
  const [copiedKey, setCopiedKey] = React.useState<string | null>(null);

  React.useEffect(() => {
    if (!copiedKey) return undefined;
    const timer = window.setTimeout(() => setCopiedKey(null), timeoutMs);
    return () => window.clearTimeout(timer);
  }, [copiedKey, timeoutMs]);

  const markCopied = React.useCallback((key: string) => {
    setCopiedKey(key);
  }, []);

  const clearCopied = React.useCallback(() => {
    setCopiedKey(null);
  }, []);

  return { clearCopied, copiedKey, markCopied };
}

export type CopyFeedbackHook = typeof useCopyFeedback;
