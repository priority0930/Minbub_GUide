"use client";

import { useRef, useState } from "react";

type ChatMessage = {
  role: "user" | "assistant";
  content: string;
};

type Material = {
  filename: string;
  text: string;
  charCount: number;
  truncated: boolean;
  pageCount?: number;
};

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [material, setMaterial] = useState<Material | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function sendToChat(nextMessages: ChatMessage[], isFirstTurnWithMaterial: boolean) {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMessages,
          material,
          isFirstTurnWithMaterial,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "응답을 받지 못했습니다.");
      }
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const res = await fetch("/api/upload", { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "업로드에 실패했습니다.");
      }
      const newMaterial: Material = {
        filename: data.filename,
        text: data.text,
        charCount: data.charCount,
        truncated: data.truncated,
        pageCount: data.pageCount,
      };
      setMaterial(newMaterial);

      const kickoffMessage: ChatMessage = {
        role: "user",
        content:
          "방금 업로드한 자료를 분석해서 세션 목차를 먼저 제시하고, 세션 1의 핵심 질문부터 시작해줘.",
      };
      const nextMessages = [...messages, kickoffMessage];
      setMessages(nextMessages);

      setLoading(true);
      setError(null);
      const chatRes = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMessages,
          material: newMaterial,
          isFirstTurnWithMaterial: true,
        }),
      });
      const chatData = await chatRes.json();
      if (!chatRes.ok) {
        throw new Error(chatData.error || "응답을 받지 못했습니다.");
      }
      setMessages([...nextMessages, { role: "assistant", content: chatData.reply }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setUploading(false);
      setLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  function handleSend() {
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    const nextMessages = [...messages, { role: "user" as const, content: trimmed }];
    setMessages(nextMessages);
    setInput("");
    sendToChat(nextMessages, false);
  }

  return (
    <main className="mx-auto flex h-screen max-w-3xl flex-col px-4 py-4">
      <header className="mb-3 flex items-center justify-between border-b border-black/10 pb-3 dark:border-white/10">
        <div>
          <h1 className="text-lg font-semibold">민법 가이드</h1>
          <p className="text-xs text-black/60 dark:text-white/60">
            변리사 1차 민법개론 학습 코치
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.txt,application/pdf,text/plain"
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading || loading}
            className="rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
          >
            {uploading ? "업로드 중..." : "PDF/TXT 업로드"}
          </button>
        </div>
      </header>

      {material && (
        <div className="mb-3 rounded-md border border-brand-100 bg-brand-50 px-3 py-2 text-xs text-brand-700 dark:border-white/10 dark:bg-white/5 dark:text-brand-100">
          자료 등록됨: <strong>{material.filename}</strong>
          {material.pageCount ? ` · ${material.pageCount}페이지` : ""} ·{" "}
          {material.charCount.toLocaleString()}자
          {material.truncated && " (분량이 많아 일부만 반영됨 — 다음 학습 묶음으로 이어집니다)"}
        </div>
      )}

      <div className="scrollbar-thin flex-1 space-y-4 overflow-y-auto py-2">
        {messages.length === 0 && (
          <div className="mt-10 text-center text-sm text-black/50 dark:text-white/50">
            학습할 PDF 또는 TXT 자료를 업로드하면 논점 단위로 세션을 나눠 코칭을 시작합니다.
          </div>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`prose-chat max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-brand-600 text-white"
                  : "bg-white text-black shadow-sm dark:bg-white/10 dark:text-white"
              }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-lg bg-white px-3 py-2 text-sm text-black/50 shadow-sm dark:bg-white/10 dark:text-white/60">
              생각하는 중...
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="mb-2 rounded-md border border-red-300 bg-red-50 px-3 py-2 text-xs text-red-700 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="flex gap-2 border-t border-black/10 pt-3 dark:border-white/10">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          rows={2}
          placeholder="답변을 입력하세요 (Shift+Enter로 줄바꿈)"
          className="flex-1 resize-none rounded-md border border-black/10 bg-white px-3 py-2 text-sm outline-none focus:border-brand-500 dark:border-white/10 dark:bg-white/5"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700 disabled:opacity-50"
        >
          전송
        </button>
      </div>
    </main>
  );
}
