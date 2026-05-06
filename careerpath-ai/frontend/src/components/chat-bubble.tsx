import { useState } from "react";

export function ChatBubble() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { from: "ai", text: "Salut! Sunt CareerPath AI. Cu ce te pot ajuta?" },
  ]);
  const [input, setInput] = useState("");

  function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages((msgs) => [...msgs, { from: "user", text: input }]);
    // Simulare răspuns AI
    setTimeout(() => {
      setMessages((msgs) => [...msgs, { from: "ai", text: "Întrebare primită! Un agent AI real va răspunde aici." }]);
    }, 800);
    setInput("");
  }

  return (
    <div className="fixed bottom-8 right-8 z-50 flex flex-col items-end">
      {open && (
        <div className="w-80 bg-white/80 backdrop-blur-lg rounded-2xl shadow-2xl border border-gray-200 mb-2 overflow-hidden flex flex-col">
          <div className="px-4 py-3 bg-gradient-to-r from-primary/80 to-blue-400/80 text-white font-bold text-lg">AI Assistant</div>
          <div className="flex-1 px-4 py-2 space-y-2 max-h-64 overflow-y-auto text-sm">
            {messages.map((msg, i) => (
              <div key={i} className={msg.from === "ai" ? "text-left" : "text-right"}>
                <span className={msg.from === "ai" ? "bg-primary/10 text-primary px-3 py-1 rounded-xl" : "bg-gray-200 text-gray-800 px-3 py-1 rounded-xl"}>{msg.text}</span>
              </div>
            ))}
          </div>
          <form onSubmit={handleSend} className="flex border-t border-gray-200">
            <input
              className="flex-1 px-3 py-2 bg-transparent outline-none text-gray-900"
              placeholder="Scrie o întrebare..."
              value={input}
              onChange={e => setInput(e.target.value)}
            />
            <button type="submit" className="px-4 text-primary font-bold">&rarr;</button>
          </form>
        </div>
      )}
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-14 h-14 rounded-full bg-white/80 backdrop-blur-lg shadow-xl border border-gray-200 flex items-center justify-center hover:scale-105 transition-transform"
        aria-label="Deschide chat AI"
      >
        <svg width="28" height="28" fill="none" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#2563eb" opacity=".15"/><path d="M8 10h.01M12 10h.01M16 10h.01M8 14h8" stroke="#2563eb" strokeWidth="2" strokeLinecap="round"/></svg>
      </button>
    </div>
  );
}
