"use client";
import { useState, useRef, useEffect, useCallback } from "react";
import Link from "next/link";
import { Send, Sparkles, Search, MessageCircleQuestion, Loader2, FileUp, ArrowRight } from "lucide-react";

const ORCHESTRATOR_WS_URL = process.env.NEXT_PUBLIC_ORCHESTRATOR_WS_URL || "ws://localhost:8005";

const initialActions = [
  { label: "Find the Right Job for Me", icon: <Sparkles size={18} /> },
  { label: "Search for a Specific Job", icon: <Search size={18} /> },
  { label: "Ask a Job-related Question", icon: <MessageCircleQuestion size={18} /> },
];

function getSessionId(): string {
  if (typeof window === "undefined") return "anon";
  let id = sessionStorage.getItem("cp_session_id");
  if (!id) {
    id = `anon_${Math.random().toString(36).slice(2, 10)}`;
    sessionStorage.setItem("cp_session_id", id);
  }
  return id;
}

function getUserId(): string {
  try {
    const raw = localStorage.getItem("auth-storage");
    if (raw) {
      const { state } = JSON.parse(raw);
      if (state?.user?.id) return state.user.id;
    }
  } catch {}
  return getSessionId();
}

type Message = { from: "ai" | "user"; text: string };
type WsStatus = "connecting" | "connected" | "disconnected";

export function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const [wsStatus, setWsStatus] = useState<WsStatus>("connecting");
  const [showCta, setShowCta] = useState(false);

  const wsRef = useRef<WebSocket | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const connect = useCallback(() => {
    const userId = getUserId();
    const ws = new WebSocket(`${ORCHESTRATOR_WS_URL}/ws/chat/${userId}`);
    wsRef.current = ws;
    setWsStatus("connecting");

    ws.onopen = () => setWsStatus("connected");

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === "typing") {
          setIsTyping(true);
        } else if (payload.type === "message") {
          setIsTyping(false);
          setMessages((prev) => [...prev, { from: "ai", text: payload.text }]);
        } else if (payload.type === "cta") {
          setIsTyping(false);
          setShowCta(true);
        }
      } catch {
        setIsTyping(false);
        setMessages((prev) => [...prev, { from: "ai", text: event.data }]);
      }
    };

    ws.onclose = () => {
      setWsStatus("disconnected");
      // Reconnect after 3s
      setTimeout(connect, 3000);
    };

    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const sendMessage = (text: string) => {
    if (!text.trim() || wsStatus !== "connected") return;
    setMessages((prev) => [...prev, { from: "user", text }]);
    setShowSuggestions(false);
    setInput("");
    wsRef.current?.send(JSON.stringify({ message: text }));
  };

  return (
    <div className="flex flex-col h-full w-full bg-transparent overflow-hidden">
      <style jsx>{`
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-track { background: transparent; }
        .custom-scroll::-webkit-scrollbar-thumb {
          background: rgba(255,255,255,0.1);
          border-radius: 10px;
        }
      `}</style>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-8 py-6 space-y-2 custom-scroll"
      >
        {/* Connecting placeholder */}
        {messages.length === 0 && wsStatus === "connecting" && (
          <div className="flex justify-start animate-in fade-in duration-500">
            <div className="px-5 py-3 rounded-[22px] bg-white/5 border border-white/5 text-slate-500 text-[13px] flex items-center gap-2">
              <Loader2 size={14} className="animate-spin" /> Connecting to AI...
            </div>
          </div>
        )}

        {/* Disconnected banner */}
        {wsStatus === "disconnected" && (
          <div className="text-center text-[11px] text-slate-600 py-1">
            Reconnecting...
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.from === "ai" ? "justify-start" : "justify-end"} animate-in fade-in duration-500`}
          >
            <div
              className={`max-w-[80%] px-5 py-3 rounded-[22px] text-[14px] leading-relaxed ${
                msg.from === "ai"
                  ? "bg-white/5 text-slate-300 border border-white/5"
                  : "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 font-medium"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="flex justify-start animate-in fade-in duration-300">
            <div className="px-5 py-3 rounded-[22px] bg-white/5 border border-white/5 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
              <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
            </div>
          </div>
        )}

        {/* CV upload CTA — shown after interview completes */}
        {showCta && (
          <div className="flex justify-start animate-in fade-in slide-in-from-bottom-4 duration-700 pt-2">
            <Link
              href="/upload"
              className="group flex items-center gap-4 px-6 py-4 rounded-[20px] bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white shadow-lg shadow-indigo-900/30 transition-all transform hover:scale-[1.02] active:scale-[0.98] max-w-sm w-full"
            >
              <div className="p-2 rounded-xl bg-white/15">
                <FileUp size={20} />
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold">Upload your CV</p>
                <p className="text-[11px] text-indigo-200 mt-0.5">Get your personalized career analysis</p>
              </div>
              <ArrowRight size={16} className="opacity-60 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        )}

        {/* Suggestion chips */}
        {showSuggestions && messages.length > 0 && wsStatus === "connected" && (
          <div className="flex flex-col gap-3 pt-2 items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            {initialActions.map((action, i) => (
              <button
                key={i}
                onClick={() => sendMessage(action.label)}
                className="w-full max-w-sm flex items-center gap-3 px-6 py-4 rounded-[20px] bg-indigo-600/90 hover:bg-indigo-500 text-white transition-all transform hover:scale-[1.02] active:scale-[0.98] shadow-lg shadow-indigo-900/20"
              >
                <span className="opacity-80">{action.icon}</span>
                <span className="text-sm font-semibold">{action.label}</span>
              </button>
            ))}
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => { e.preventDefault(); sendMessage(input); }}
        className="p-6 bg-white/[0.01] border-t border-white/5"
      >
        <div className="relative flex items-center bg-white/5 border border-white/10 rounded-[22px] focus-within:border-indigo-500/40 focus-within:bg-white/[0.08] transition-all">
          <input
            className="w-full pl-6 pr-12 py-4 bg-transparent outline-none text-white placeholder:text-slate-500 text-sm"
            placeholder={wsStatus === "connected" ? "Tell me about your career goals..." : "Connecting..."}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={wsStatus !== "connected"}
          />
          <button
            type="submit"
            disabled={wsStatus !== "connected" || !input.trim()}
            className="absolute right-3 p-2 text-indigo-400 hover:text-white transition-colors disabled:opacity-30"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
