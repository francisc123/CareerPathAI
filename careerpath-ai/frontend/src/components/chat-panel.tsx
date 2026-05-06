"use client";
import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, Search, MessageCircleQuestion } from "lucide-react";

const initialActions = [
  { label: "Search for a Specific Job", icon: <Search size={18} /> },
  { label: "Find the Right Job for Me", icon: <Sparkles size={18} /> },
  { label: "Ask a Job-related Question", icon: <MessageCircleQuestion size={18} /> },
];

export function ChatPanel() {
  const [messages, setMessages] = useState([
    { from: "ai", text: "Hello! I am CareerPath AI. How can I assist your career today?" },
  ]);
  const [input, setInput] = useState("");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const processSend = (text: string) => {
    if (!text.trim()) return;
    setMessages((prev) => [...prev, { from: "user", text }]);
    setShowSuggestions(false);
    setInput("");

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { from: "ai", text: "Analyzing your request... I will generate a personalized response shortly." },
      ]);
    }, 800);
  };

  return (
    <div className="flex flex-col h-full w-full bg-transparent overflow-hidden">
      <style jsx>{`
        .custom-scroll::-webkit-scrollbar { width: 4px; }
        .custom-scroll::-webkit-scrollbar-track { background: transparent; }
        .custom-scroll::-webkit-scrollbar-thumb { 
          background: rgba(255, 255, 255, 0.1); 
          border-radius: 10px; 
        }
      `}</style>

      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto px-8 py-6 space-y-2 custom-scroll"
      >
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.from === "ai" ? "justify-start" : "justify-end"} animate-in fade-in duration-500`}>
            <div className={`max-w-[80%] px-5 py-3 rounded-[22px] text-[14px] leading-relaxed ${
              msg.from === "ai" 
                ? "bg-white/5 text-slate-300 border border-white/5" 
                : "bg-indigo-600 text-white shadow-lg shadow-indigo-500/20 font-medium"
            }`}>
              {msg.text}
            </div>
          </div>
        ))}

        {showSuggestions && (
          <div className="flex flex-col gap-3 pt-2 items-center justify-center animate-in fade-in slide-in-from-bottom-4 duration-700">
            {initialActions.map((action, i) => (
              <button
                key={i}
                onClick={() => processSend(action.label)}
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
        onSubmit={(e) => { e.preventDefault(); processSend(input); }} 
        className="p-6 bg-white/[0.01] border-t border-white/5"
      >
        <div className="relative flex items-center bg-white/5 border border-white/10 rounded-[22px] focus-within:border-indigo-500/40 focus-within:bg-white/[0.08] transition-all">
          <input
            className="w-full pl-6 pr-12 py-4 bg-transparent outline-none text-white placeholder:text-slate-500 text-sm"
            placeholder="How can we help you?"
            value={input}
            onChange={e => setInput(e.target.value)}
          />
          <button type="submit" className="absolute right-3 p-2 text-indigo-400 hover:text-white transition-colors">
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}