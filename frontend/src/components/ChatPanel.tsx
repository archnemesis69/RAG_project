import { useRef, useState, type FormEvent } from "react";
import { sendQuery } from "../api/client";
import type { ChatMessage } from "../types";

interface Props {
  hasReadyDocuments: boolean;
}

export function ChatPanel({ hasReadyDocuments }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const idCounter = useRef(0);

  function nextId(): string {
    idCounter.current += 1;
    return `msg-${idCounter.current}`;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || isAsking) return;

    setMessages((prev) => [...prev, { id: nextId(), role: "user", content: trimmed }]);
    setQuestion("");
    setIsAsking(true);

    try {
      const result = await sendQuery(trimmed);
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: "assistant", content: result.answer, sources: result.sources },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: "assistant",
          content: "I couldn't reach the AI service. Check that it's running and try again.",
        },
      ]);
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <section className="chat-panel">
      {messages.length === 0 ? (
        <div className="chat-empty">
          <p className="chat-empty-title">Ask about your documents</p>
          <p className="chat-empty-body">
            {hasReadyDocuments
              ? "Try asking something specific — the answer will cite exactly where it came from."
              : "Import a document on the left, then ask a question once it's ready."}
          </p>
        </div>
      ) : (
        <div className="chat-messages">
          {messages.map((message) => (
            <div key={message.id} className={`chat-message chat-message-${message.role}`}>
              <p className="chat-message-content">{message.content}</p>
              {message.sources && message.sources.length > 0 && (
                <div className="citation-row">
                  {message.sources.map((source, i) => (
                    <span className="citation-chip" key={`${message.id}-${i}`}>
                      {source.source ?? "unknown"}
                      {source.page != null ? ` · p.${source.page}` : ""}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Ask a question about your documents…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={isAsking}
        />
        <button type="submit" className="btn-primary" disabled={isAsking || !question.trim()}>
          {isAsking ? "Thinking…" : "Ask"}
        </button>
      </form>
    </section>
  );
}
