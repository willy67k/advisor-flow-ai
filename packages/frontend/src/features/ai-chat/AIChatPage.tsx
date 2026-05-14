import { useCallback, useEffect, useRef, useState } from "react";

import { useAuthStore } from "../../stores/authStore";

interface ToolEvent {
  readonly tool: string;
  readonly startedAt: number;
  readonly endedAt?: number;
  readonly durationMs?: number;
}

interface ChatMessage {
  readonly id: string;
  readonly role: "user" | "assistant";
  content: string;
  readonly toolEvents: ToolEvent[];
  readonly isStreaming: boolean;
}

type StreamEvent = { type: "token"; content: string } | { type: "tool_start"; tool: string } | { type: "tool_end"; tool: string; duration_ms: number } | { type: "done" } | { type: "error"; message: string };

function uid() {
  return Math.random().toString(36).slice(2);
}

export function AIChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const accessToken = useAuthStore((s) => s.accessToken);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || streaming) return;
      setConnectionError(null);

      const userMsg: ChatMessage = {
        id: uid(),
        role: "user",
        content: text.trim(),
        toolEvents: [],
        isStreaming: false,
      };

      const assistantId = uid();
      const assistantMsg: ChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        toolEvents: [],
        isStreaming: true,
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setInput("");
      setStreaming(true);

      const ctrl = new AbortController();
      abortRef.current = ctrl;

      try {
        const res = await fetch("/api/chat/stream", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "text/event-stream",
            Authorization: `Bearer ${accessToken ?? ""}`,
          },
          body: JSON.stringify({ message: text.trim() }),
          signal: ctrl.signal,
        });

        if (!res.ok || !res.body) {
          throw new Error(res.status === 404 ? "AI Chat endpoint is not yet available." : `Server error ${res.status}.`);
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split("\n\n");
          buffer = parts.pop() ?? "";

          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith("data:")) continue;
            const json = line.slice(5).trim();
            if (!json || json === "[DONE]") continue;

            let evt: StreamEvent;
            try {
              evt = JSON.parse(json) as StreamEvent;
            } catch {
              continue;
            }

            setMessages((prev) =>
              prev.map((m) => {
                if (m.id !== assistantId) return m;
                if (evt.type === "token") {
                  return { ...m, content: m.content + evt.content };
                }
                if (evt.type === "tool_start") {
                  return {
                    ...m,
                    toolEvents: [...m.toolEvents, { tool: evt.tool, startedAt: Date.now() }],
                  };
                }
                if (evt.type === "tool_end") {
                  return {
                    ...m,
                    toolEvents: m.toolEvents.map((te) => (te.tool === evt.tool && !te.endedAt ? { ...te, endedAt: Date.now(), durationMs: evt.duration_ms } : te)),
                  };
                }
                if (evt.type === "done") {
                  return { ...m, isStreaming: false };
                }
                if (evt.type === "error") {
                  return { ...m, content: m.content || evt.message, isStreaming: false };
                }
                return m;
              }),
            );

            if (evt.type === "done" || evt.type === "error") break;
          }
        }
      } catch (err: unknown) {
        if ((err as Error)?.name === "AbortError") {
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: m.content || "—", isStreaming: false } : m)));
        } else {
          const msg = err instanceof Error ? err.message : "Unable to reach the AI service.";
          setConnectionError(msg);
          setMessages((prev) => prev.map((m) => (m.id === assistantId ? { ...m, content: msg, isStreaming: false } : m)));
        }
      } finally {
        setStreaming(false);
        abortRef.current = null;
      }
    },
    [streaming, accessToken],
  );

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void sendMessage(input);
    }
  }

  function stopStream() {
    abortRef.current?.abort();
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem-4rem)] flex-col">
      <div className="mb-4 flex-shrink-0">
        <h1 className="text-xl font-semibold tracking-tight text-white">AI Chat</h1>
        <p className="mt-1 text-sm text-slate-400">Ask questions about your meetings, clients, or documents.</p>
      </div>

      <div className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-800 bg-slate-900/60">
        <div className="flex-1 space-y-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex h-full items-center justify-center">
              <div className="text-center">
                <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500/10">
                  <svg className="h-5 w-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                  </svg>
                </div>
                <p className="text-sm font-medium text-slate-400">Start a conversation</p>
                <p className="mt-1 text-xs text-slate-600">Ask about meeting summaries, client portfolios, or document analysis.</p>
              </div>
            </div>
          ) : (
            messages.map((msg) => <ChatBubble key={msg.id} message={msg} />)
          )}
          <div ref={bottomRef} />
        </div>

        {connectionError ? (
          <div className="border-t border-slate-800 bg-rose-950/20 px-4 py-2">
            <p className="text-xs text-rose-400">{connectionError}</p>
          </div>
        ) : null}

        <div className="border-t border-slate-800 p-4">
          <div className="flex gap-3">
            <textarea
              className="flex-1 resize-none rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white ring-emerald-500/40 outline-none placeholder:text-slate-600 focus:ring-2 disabled:opacity-50"
              disabled={streaming}
              placeholder="Ask something… (Enter to send, Shift+Enter for newline)"
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            {streaming ? (
              <button className="rounded-lg border border-slate-600 px-4 py-2 text-sm font-medium text-slate-300 hover:border-slate-500 hover:bg-slate-800" type="button" onClick={stopStream}>
                Stop
              </button>
            ) : (
              <button className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-emerald-950 transition hover:bg-emerald-400 disabled:opacity-50" disabled={!input.trim()} type="button" onClick={() => void sendMessage(input)}>
                Send
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function ChatBubble({ message }: { readonly message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 py-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${isUser ? "bg-slate-700 text-slate-200" : "bg-emerald-500/20 text-emerald-400"}`}>{isUser ? "You" : "AI"}</div>

      <div className={`max-w-[75%] space-y-2 ${isUser ? "items-end" : "items-start"} flex flex-col`}>
        {message.toolEvents.length > 0 ? <ToolTimeline events={message.toolEvents} /> : null}

        <div className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${isUser ? "rounded-tr-sm bg-slate-700 text-slate-100" : "rounded-tl-sm bg-slate-800/80 text-slate-200"}`}>
          {message.content || (message.isStreaming ? null : "—")}
          {message.isStreaming ? <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-emerald-400 align-middle" /> : null}
        </div>
      </div>
    </div>
  );
}

function ToolTimeline({ events }: { readonly events: readonly ToolEvent[] }) {
  return (
    <div className="rounded-lg border border-slate-700/60 bg-slate-900 px-3 py-2 text-xs">
      <p className="mb-1.5 text-[10px] font-semibold tracking-wide text-slate-500 uppercase">Tool calls</p>
      <ul className="space-y-1.5">
        {events.map((evt, idx) => (
          <li key={`${evt.tool}-${idx}`} className="flex items-center gap-2">
            {evt.endedAt ? <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" /> : <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />}
            <span className="font-mono text-slate-300">{evt.tool}</span>
            {evt.durationMs !== undefined ? <span className="text-slate-600">{evt.durationMs}ms</span> : <span className="text-amber-400/70">running…</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
