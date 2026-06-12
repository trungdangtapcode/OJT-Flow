import type {
  AssistantResponse,
  AssistantStreamEvent,
  AssistantToolResult,
} from "../../types";
import { formatCount } from "./assistant-format";

export type PlannerStreamPlan = {
  message: string;
  toolCalls: {
    arguments: Record<string, unknown>;
    rationale: string;
    toolName: string;
  }[];
  warnings: string[];
};

export function planningStartedDetail(
  event: Extract<AssistantStreamEvent, { type: "planning_started" }>,
): string {
  const parts = [
    event.message,
    event.model ? `Model: ${event.model}.` : null,
    typeof event.available_tool_count === "number"
      ? `Tools available: ${event.available_tool_count}.`
      : null,
    typeof event.max_tool_calls === "number" ? `Max tool calls: ${event.max_tool_calls}.` : null,
  ].filter((part): part is string => Boolean(part));
  return parts.join(" ");
}

export function formatPlannerStreamText(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) {
    return "Waiting for planner tokens...";
  }
  try {
    const parsed = JSON.parse(trimmed);
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) {
      return formattedPlannerObject(parsed as Record<string, unknown>);
    }
  } catch {
    return trimmed.length > 4000 ? trimmed.slice(-4000) : trimmed;
  }
  return trimmed.length > 4000 ? trimmed.slice(-4000) : trimmed;
}

export function plannerStreamPlan(text: string): PlannerStreamPlan | null {
  const trimmed = text.trim();
  if (!trimmed) return null;
  try {
    const parsed = JSON.parse(trimmed);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    const record = parsed as Record<string, unknown>;
    const toolCalls = Array.isArray(record.tool_calls) ? record.tool_calls : [];
    const warnings = Array.isArray(record.warnings)
      ? record.warnings.filter((item): item is string => typeof item === "string")
      : [];
    return {
      message: typeof record.message === "string" ? record.message : "",
      toolCalls: toolCalls
        .map(plannerToolCallValue)
        .filter((item): item is PlannerStreamPlan["toolCalls"][number] => item !== null),
      warnings,
    };
  } catch {
    return null;
  }
}

export function plannerArgumentPreview(value: unknown): string {
  if (typeof value === "string") {
    const payload = structuredPayloadPreview(value);
    if (payload) return payload;
    const clean = value.replace(/\s+/g, " ").trim();
    return clean.length > 28 ? `${clean.slice(0, 28)}...` : clean || "empty";
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return formatCount(value.length, "item");
  }
  if (value && typeof value === "object") {
    return formatCount(Object.keys(value).length, "field");
  }
  return "null";
}

export function completedToolResultByIndex(
  streamEvents: AssistantStreamEvent[],
  response: AssistantResponse | null,
): Map<number, AssistantToolResult> {
  const completed = new Map<number, AssistantToolResult>();
  for (const event of streamEvents) {
    if (event.type === "tool_completed") {
      completed.set(event.index, event.tool_result);
    }
  }
  if (!completed.size && response) {
    response.tool_calls.forEach((result, index) => {
      completed.set(index + 1, result);
    });
  }
  return completed;
}

function plannerToolCallValue(value: unknown): PlannerStreamPlan["toolCalls"][number] | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const toolName = typeof record.tool_name === "string" ? record.tool_name : "";
  if (!toolName) return null;
  return {
    arguments: plannerArgumentsValue(record),
    rationale: typeof record.rationale === "string" ? record.rationale : "",
    toolName,
  };
}

function plannerArgumentsValue(record: Record<string, unknown>): Record<string, unknown> {
  if (record.arguments && typeof record.arguments === "object" && !Array.isArray(record.arguments)) {
    return record.arguments as Record<string, unknown>;
  }
  if (typeof record.arguments_json === "string") {
    try {
      const parsed = JSON.parse(record.arguments_json);
      return parsed && typeof parsed === "object" && !Array.isArray(parsed)
        ? (parsed as Record<string, unknown>)
        : {};
    } catch {
      return { arguments_json: record.arguments_json };
    }
  }
  return {};
}

function structuredPayloadPreview(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed) return "empty";
  const lines = trimmed.split(/\r?\n/).filter((line) => line.trim());
  const looksCsv =
    lines.length > 1 &&
    lines[0].includes(",") &&
    lines.slice(1).some((line) => line.includes(","));
  if (looksCsv) {
    return `CSV ${formatCount(Math.max(0, lines.length - 1), "row")}`;
  }
  if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) return `JSON ${formatCount(parsed.length, "item")}`;
      if (parsed && typeof parsed === "object") {
        return `JSON ${formatCount(Object.keys(parsed).length, "field")}`;
      }
    } catch {
      return null;
    }
  }
  if (trimmed.length > 120 || lines.length > 3) {
    return `${formatCount(trimmed.length, "char")} payload`;
  }
  return null;
}

function formattedPlannerObject(value: Record<string, unknown>): string {
  const lines: string[] = [];
  const message = typeof value.message === "string" ? value.message.trim() : "";
  if (message) {
    lines.push(`Message: ${message}`);
  }
  const toolCalls = Array.isArray(value.tool_calls) ? value.tool_calls : [];
  if (toolCalls.length) {
    lines.push("Tools:");
    toolCalls.forEach((item, index) => {
      if (!item || typeof item !== "object" || Array.isArray(item)) return;
      const record = item as Record<string, unknown>;
      const toolName = typeof record.tool_name === "string" ? record.tool_name : "tool";
      const rationale =
        typeof record.rationale === "string" && record.rationale.trim()
          ? ` - ${record.rationale.trim()}`
          : "";
      lines.push(`${index + 1}. ${toolName}${rationale}`);
      const args = plannerArgumentsText(record);
      if (args) lines.push(`   args: ${args}`);
    });
  } else {
    lines.push("Tools: none selected yet");
  }
  const warnings = Array.isArray(value.warnings)
    ? value.warnings.filter((item): item is string => typeof item === "string")
    : [];
  if (warnings.length) {
    lines.push("Warnings:");
    warnings.forEach((warning) => lines.push(`- ${warning}`));
  }
  return lines.join("\n");
}

function plannerArgumentsText(record: Record<string, unknown>): string {
  if (record.arguments && typeof record.arguments === "object") {
    return JSON.stringify(record.arguments);
  }
  if (typeof record.arguments_json === "string") {
    try {
      return JSON.stringify(JSON.parse(record.arguments_json));
    } catch {
      return record.arguments_json;
    }
  }
  return "";
}
