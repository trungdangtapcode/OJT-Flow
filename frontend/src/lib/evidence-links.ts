export function evidenceAnchorId(evidenceId: string) {
  return `evidence-${anchorToken(evidenceId)}`;
}

export function assistantEvidenceAnchorId(evidenceId: string) {
  return `assistant-${evidenceAnchorId(evidenceId)}`;
}

export function workflowEventAnchorId(eventId: string) {
  return `workflow-event-${anchorToken(eventId)}`;
}

export function validationIssueAnchorId(issueId: string) {
  return `validation-issue-${anchorToken(issueId)}`;
}

export function workflowEvidenceHref(workflowId: string, evidenceId: string) {
  return `/workflows/${encodeURIComponent(workflowId)}#${evidenceAnchorId(evidenceId)}`;
}

export function workflowEventHref(workflowId: string, eventId: string) {
  return `/workflows/${encodeURIComponent(workflowId)}#${workflowEventAnchorId(eventId)}`;
}

export function retrievalEvidenceHref(evidenceId: string) {
  return `/retrieval#${evidenceAnchorId(evidenceId)}`;
}

function anchorToken(value: string) {
  const sanitized = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return sanitized || hashText(value);
}

function hashText(value: string) {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash * 31 + value.charCodeAt(index)) >>> 0;
  }
  return hash.toString(16).padStart(8, "0");
}
