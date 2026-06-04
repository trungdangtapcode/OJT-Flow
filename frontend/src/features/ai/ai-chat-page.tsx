import * as React from "react";
import { Bot, ChevronDown, ChevronRight, Loader2, Send, Wrench } from "lucide-react";
import { fetchAiStatus, sendAiChat } from "../../api";
import type { AiChatMessage, AiToolCall } from "../../types";
import { Button } from "../../components/ui/button";
import { PageHeader } from "../../components/layout/page-header";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: AiToolCall[];
  error?: string;
};

function ToolCallBadge({ tc }: { tc: AiToolCall }) {
  const [open, setOpen] = React.useState(false);
  return (
    <div className="mt-1 rounded border border-border bg-muted/40 text-xs">
      <button
        className="flex w-full items-center gap-1.5 px-2 py-1 text-left font-mono text-muted-foreground hover:text-foreground"
        onClick={() => setOpen(!open)}
        type="button"
      >
        <Wrench className="h-3 w-3 shrink-0" />
        <span className="font-semibold">{tc.name}</span>
        {open ? <ChevronDown className="ml-auto h-3 w-3" /> : <ChevronRight className="ml-auto h-3 w-3" />}
      </button>
      {open && (
        <pre className="overflow-x-auto border-t border-border px-2 py-1.5 text-[10px] leading-relaxed text-muted-foreground">
          {JSON.stringify(tc.arguments, null, 2)}
        </pre>
      )}
    </div>
  );
}

function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === "user";
  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-card border border-border text-foreground"
          }`}
        >
          {msg.error ? (
            <span className="text-destructive">{msg.error}</span>
          ) : (
            msg.content
          )}
        </div>
        {msg.toolCalls && msg.toolCalls.length > 0 && (
          <div className="mt-1 space-y-0.5">
            {msg.toolCalls.map((tc, i) => (
              <ToolCallBadge key={i} tc={tc} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function AiChatPage() {
  const [messages, setMessages] = React.useState<Message[]>([]);
  const [input, setInput] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [aiReady, setAiReady] = React.useState<boolean | null>(null);
  const [model, setModel] = React.useState("");
  const bottomRef = React.useRef<HTMLDivElement>(null);
  const textareaRef = React.useRef<HTMLTextAreaElement>(null);

  React.useEffect(() => {
    fetchAiStatus()
      .then((s) => { setAiReady(s.configured); setModel(s.model); })
      .catch(() => setAiReady(false));
  }, []);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    const history: AiChatMessage[] = messages.map((m) => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const res = await sendAiChat({ message: text, history });
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: res.answer,
          toolCalls: res.tool_calls,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "",
          error: err instanceof Error ? err.message : "Request failed.",
        },
      ]);
    } finally {
      setLoading(false);
      textareaRef.current?.focus();
    }
  };

  const handleKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send();
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col gap-0">
      <PageHeader
        title="AI Assistant"
        description="Ask about your data in natural language. The AI uses OJTFlow tools to validate, convert, and explain."
      />

      {aiReady === false && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          AI gateway is not configured. Set <code className="font-mono">GROQ_API_KEY</code> in your <code className="font-mono">.env</code> file and restart the backend.
        </div>
      )}

      {aiReady && model && (
        <div className="mb-2 flex items-center gap-2 text-xs text-muted-foreground">
          <Bot className="h-3 w-3" />
          <span>{model}</span>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-border bg-background p-4">
        {messages.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center gap-3 text-center text-muted-foreground">
            <Bot className="h-10 w-10 opacity-30" />
            <div>
              <p className="font-semibold">Ask about your healthcare data</p>
              <p className="mt-1 text-sm opacity-70">
                Try: <em>"Validate this CSV: date,patient_id,value\n2026-01-01,P001,7.4"</em>
              </p>
              <p className="mt-0.5 text-sm opacity-70">
                Or: <em>"Convert this JSON to CSV: [{'{'}\"name\":\"HbA1c\",\"value\":7.4{'}'}]"</em>
              </p>
            </div>
          </div>
        )}
        <div className="space-y-4">
          {messages.map((msg) => (
            <ChatMessage key={msg.id} msg={msg} />
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking…</span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div className="mt-3 flex gap-2">
        <textarea
          ref={textareaRef}
          className="flex-1 resize-none rounded-xl border border-border bg-card px-3.5 py-2.5 text-sm shadow-sm outline-none placeholder:text-muted-foreground focus:ring-2 focus:ring-primary/30"
          disabled={loading || aiReady === false}
          onKeyDown={handleKey}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about your data… (Enter to send, Shift+Enter for newline)"
          rows={2}
          value={input}
        />
        <Button
          className="self-end"
          disabled={!input.trim() || loading || aiReady === false}
          onClick={() => void send()}
          size="icon"
          type="button"
        >
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
