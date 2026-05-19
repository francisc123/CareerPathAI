"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useAuthStore } from "@/store/auth.store";
import {
  MessageSquare,
  Send,
  Sparkles,
  User,
  StopCircle,
  Award,
  Activity,
  ThumbsUp,
  BrainCircuit,
  MessageCircle,
  Lock,
  BookOpen,
  Zap,
  CheckCircle2,
  XCircle
} from "lucide-react";
import { cn } from "@/lib/utils";

type WSStatus = "connecting" | "connected" | "disconnected";
type InterviewState = "ongoing" | "completed";
type Verdict = "PASS" | "FAIL" | null;

interface ChatMessage { from: "ai" | "user"; text: string; }
interface HRFeedback {
  verdict: Verdict;
  summary: string;
  strengths: string[];
  areasOfImprovement: string[];
}

function hasCvAnalysis(): boolean {
  if (typeof window === "undefined") return false;
  try {
    const raw = localStorage.getItem("careerpath_cv_analysis");
    if (!raw) return false;
    const v = JSON.parse(raw);
    return typeof v?.score === "number";
  } catch {
    return false;
  }
}

export default function HRInterviewPage() {
  // Unlock-ul real: necesită un CV analizat (avem score + target_role). Dev
  // unlock-ul rămâne pentru cazuri de regresie.
  const [hasPassedQuiz, setHasPassedQuiz] = useState(false);
  useEffect(() => {
    if (hasCvAnalysis()) setHasPassedQuiz(true);
  }, []);
  const [wsStatus, setWsStatus] = useState<WSStatus>("connecting");
  const [interviewState, setInterviewState] = useState<InterviewState>("ongoing");
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isAiTyping, setIsAiTyping] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [feedback, setFeedback] = useState<HRFeedback | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const token = useAuthStore((s) => s.token);

  useEffect(() => {
    if (!hasPassedQuiz) return;
    const newSessionId = crypto.randomUUID ? crypto.randomUUID() : `mock-uuid-${Date.now()}`;
    setSessionId(newSessionId);
    setMessages([]);
  }, [hasPassedQuiz]);

  const connectWS = useCallback(() => {
    if (!sessionId || !hasPassedQuiz || !token) return;
    const wsUrl = process.env.NEXT_PUBLIC_HR_WS_URL || `ws://localhost:8000/ws/hr-interview/${sessionId}?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onopen = () => setWsStatus("connected");
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        switch (data.type) {
          case "chat_message":
            setIsAiTyping(false);
            setMessages((prev) => [...prev, { from: "ai", text: data.text || "" }]);
            break;
          case "interview_complete":
            setIsAiTyping(false);
            setFeedback({
              verdict: (data.verdict === "PASS" || data.verdict === "FAIL") ? data.verdict : null,
              summary: data.summary || "",
              strengths: Array.isArray(data.strengths) ? data.strengths : [],
              areasOfImprovement: Array.isArray(data.areas_of_improvement) ? data.areas_of_improvement : [],
            });
            setInterviewState("completed");
            break;
        }
      } catch (err) { console.error(err); }
    };
    ws.onclose = () => { setWsStatus("disconnected"); setTimeout(connectWS, 5000); };
    ws.onerror = () => ws.close();
  }, [sessionId, hasPassedQuiz, token]);

  useEffect(() => {
    if (hasPassedQuiz) connectWS();
    return () => wsRef.current?.close();
  }, [connectWS, hasPassedQuiz]);

  useEffect(() => {
    if (chatScrollRef.current) chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
  }, [messages, isAiTyping]);

  const adjustTextareaHeight = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  };

  const handleSendMessage = () => {
    const text = chatInput.trim();
    if (!text || isAiTyping) return;
    setMessages(prev => [...prev, { from: "user", text }]);
    setChatInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    if (wsRef.current && wsStatus === "connected") {
      setIsAiTyping(true);
      wsRef.current.send(JSON.stringify({ type: "chat_message", text }));
    } else {
      // Dev/offline fallback — no live WS. Surface a single mock reply and let
      // the user trigger completion explicitly via End Interview.
      setIsAiTyping(true);
      setTimeout(() => {
        const mockResponse = "That's a very interesting perspective. Can you give me a specific example of a time when you had to deal with a difficult team member to achieve that outcome?";
        setMessages(prev => [...prev, { from: "ai", text: mockResponse }]);
        setIsAiTyping(false);
      }, 600);
    }
  };

  const triggerInterviewComplete = () => {
    if (wsRef.current && wsStatus === "connected") {
      wsRef.current.send(JSON.stringify({ type: "end_interview" }));
    } else {
      setFeedback({
        verdict: "PASS",
        summary: "The candidate demonstrated coherent answers with clear Situation + Action coverage and owned their contribution. Tone was professional throughout. Verdict: PASS.",
        strengths: [
          "Clear and concise articulation of complex situations",
          "Strong emphasis on team collaboration",
        ],
        areasOfImprovement: ["Could provide more quantifiable metrics in future answers"],
      });
      setInterviewState("completed");
    }
  };

  // LOCKED STATE
  if (!hasPassedQuiz) {
    return (
      <div className="w-full h-[calc(100vh-170px)] flex flex-col items-center justify-center p-1 animate-in zoom-in-95 duration-500">
        <div className="max-w-md w-full bg-[#0b0f1a]/80 border border-white/5 rounded-[28px] p-10 flex flex-col items-center text-center shadow-2xl backdrop-blur-xl relative overflow-hidden">
          <div className="w-16 h-16 rounded-[20px] bg-rose-500/10 flex items-center justify-center text-rose-400 border border-rose-500/20 mb-6 shadow-inner"><Lock size={24} /></div>
          <h2 className="text-xl font-black uppercase tracking-tight text-white mb-2">Interview Locked</h2>
          <p className="text-xs font-medium text-slate-400 mb-6">Încarcă întâi un CV — interviul HR foloseste contextul tău (role, seniority, gaps).</p>
          <Link href="/upload" className="w-full py-3.5 bg-white text-black hover:bg-indigo-500 hover:text-white rounded-xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 transition-all"><BookOpen size={12} /> Upload CV</Link>
          <button onClick={() => setHasPassedQuiz(true)} className="mt-4 text-[8px] font-black text-slate-600 uppercase tracking-widest hover:text-white transition-colors">[Dev Unlock]</button>
        </div>
      </div>
    );
  }

  // COMPLETED STATE
  if (interviewState === "completed" && feedback) {
    return (
      <div className="w-full h-[calc(100vh-170px)] flex flex-col gap-5 overflow-hidden max-w-[1200px] mx-auto min-h-0 p-1 animate-in zoom-in-95 duration-500">
        <div className="flex justify-between items-center bg-[#0b0f1a]/60 border border-white/5 p-5 rounded-[24px] shadow-lg backdrop-blur-xl shrink-0">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-[14px] bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20 shadow-inner"><Award size={20} /></div>
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-indigo-400">
                 <Sparkles size={14} className="fill-current" />
                 <span className="text-[9px] font-black uppercase tracking-[0.3em]">Evaluation Complete</span>
              </div>
              <h1 className="text-2xl font-black tracking-tight text-white uppercase leading-none">Behavioral Assessment</h1>
            </div>
          </div>
          <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest shrink-0">Soft skills logged</span>
        </div>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-5 min-h-0">
          <div className="flex flex-col bg-[#0b0f1a]/60 border border-white/5 rounded-[28px] p-6 shadow-2xl backdrop-blur-xl h-full overflow-hidden">
            <div className="flex items-center gap-2 text-slate-400 mb-5 shrink-0 border-b border-white/5 pb-3"><Activity size={14}/><span className="text-[10px] font-black uppercase tracking-widest">Final Verdict</span></div>
            <VerdictBadge verdict={feedback.verdict} />
            <div className="mt-6 flex flex-col flex-1 min-h-0">
              <h3 className="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-2 shrink-0">Evaluator Summary</h3>
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2"><p className="text-[13px] font-medium text-slate-300 leading-relaxed">{feedback.summary}</p></div>
            </div>
          </div>
          <div className="flex flex-col gap-5 h-full min-h-0">
            <div className="flex-1 flex flex-col bg-[#0b0f1a]/60 border border-emerald-500/10 rounded-[28px] p-6 shadow-2xl backdrop-blur-xl min-h-0">
              <div className="flex items-center gap-2 text-emerald-400 mb-4 shrink-0"><ThumbsUp size={16}/><h3 className="text-[10px] font-black uppercase tracking-widest">Key Strengths</h3></div>
              <ul className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-3">{feedback.strengths.map((str, i) => <li key={i} className="flex items-start gap-2.5 text-xs font-medium text-slate-200"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />{str}</li>)}</ul>
            </div>
            <div className="flex-1 flex flex-col bg-[#0b0f1a]/60 border border-amber-500/10 rounded-[28px] p-6 shadow-2xl backdrop-blur-xl min-h-0">
              <div className="flex items-center gap-2 text-amber-400 mb-4 shrink-0"><TargetIcon size={16}/><h3 className="text-[10px] font-black uppercase tracking-widest">Areas for Growth</h3></div>
              <ul className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-3">{feedback.areasOfImprovement.map((imp, i) => <li key={i} className="flex items-start gap-2.5 text-xs font-medium text-slate-200"><div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />{imp}</li>)}</ul>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // LIVE INTERVIEW ENVIRONMENT - CU CHENARUL FORMATAT PREMIUM
  return (
    <div className="w-full h-[calc(100vh-170px)] flex flex-col gap-5 overflow-hidden max-w-[1200px] mx-auto min-h-0 p-1 animate-in fade-in duration-500">
      
      {/* CHENAR DESIGN TITLU UNIFICAT */}
      <div className="flex justify-between items-center bg-[#0b0f1a]/60 border border-white/5 p-5 rounded-[24px] shadow-lg backdrop-blur-xl shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-[14px] bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 shadow-inner">
            <MessageSquare size={18} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-indigo-400">
               <Sparkles size={14} className="fill-current" />
               <span className="text-[9px] font-black uppercase tracking-[0.3em]">Behavioral Node</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white uppercase leading-none">HR Behavioral Interview</h1>
          </div>
        </div>

        <div className="flex items-center gap-6 shrink-0">
          <button onClick={triggerInterviewComplete} className="px-5 py-2.5 rounded-[12px] font-black text-[10px] uppercase tracking-[0.15em] transition-all flex items-center gap-2 text-red-400 bg-red-500/10 hover:bg-red-500 hover:text-white border border-red-500/20 active:scale-95 outline-none"><StopCircle size={12} /> End Interview</button>
        </div>
      </div>

      {/* CHAT AREA */}
      <div className="flex-1 flex flex-col bg-[#0b0f1a]/60 border border-white/[0.06] rounded-[28px] overflow-hidden shadow-2xl backdrop-blur-xl min-h-0">
        <div ref={chatScrollRef} className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 min-h-0">
          {messages.map((msg, i) => <ChatBubble key={i} from={msg.from} text={msg.text} />)}
          {isAiTyping && <TypingIndicator />}
        </div>
        <div className="p-4 bg-white/[0.01] border-t border-white/5 shrink-0">
          <div className="relative flex items-end gap-3 bg-[#020617] border border-white/10 focus-within:border-indigo-500/40 rounded-xl p-2 shadow-inner">
            <textarea ref={textareaRef} value={chatInput} onChange={adjustTextareaHeight} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendMessage(); } }} placeholder={isAiTyping ? "AI is thinking..." : "Type your answer... (Shift + Enter for new line)"} disabled={isAiTyping} rows={1} className="w-full bg-transparent border-none outline-none text-sm font-medium text-white resize-none custom-scrollbar pl-4 py-2 placeholder:text-slate-600 disabled:opacity-50" />
            <button onClick={handleSendMessage} disabled={!chatInput.trim() || isAiTyping} className={cn("p-3 rounded-lg flex items-center justify-center shrink-0 transition-all", chatInput.trim() && !isAiTyping ? "bg-indigo-600 text-white" : "bg-white/5 text-slate-500")}><Send size={14} /></button>
          </div>
        </div>
      </div>
    </div>
  );
}

function VerdictBadge({ verdict }: { verdict: Verdict }) {
  if (verdict === "PASS") {
    return (
      <div className="flex items-center justify-center gap-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-6 shrink-0">
        <CheckCircle2 size={36} className="text-emerald-400 shrink-0" />
        <div className="flex flex-col">
          <span className="text-[10px] font-black text-emerald-300 uppercase tracking-[0.3em]">Verdict</span>
          <span className="text-3xl font-black text-emerald-400 tracking-tight">PASS</span>
        </div>
      </div>
    );
  }
  if (verdict === "FAIL") {
    return (
      <div className="flex items-center justify-center gap-4 bg-rose-500/10 border border-rose-500/30 rounded-2xl p-6 shrink-0">
        <XCircle size={36} className="text-rose-400 shrink-0" />
        <div className="flex flex-col">
          <span className="text-[10px] font-black text-rose-300 uppercase tracking-[0.3em]">Verdict</span>
          <span className="text-3xl font-black text-rose-400 tracking-tight">FAIL</span>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-center justify-center gap-4 bg-white/[0.02] border border-white/10 rounded-2xl p-6 shrink-0">
      <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Verdict unavailable</span>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex flex-col max-w-[85%] mr-auto items-start">
      <div className="flex items-center gap-1.5 mb-1 px-1">
        <div className="w-4 h-4 rounded-full bg-indigo-500/20 flex items-center justify-center">
          <Sparkles size={8} className="text-indigo-400" />
        </div>
        <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">AI Recruiter</span>
      </div>
      <div className="px-4 py-3 rounded-[20px] bg-white/[0.04] border border-white/5 rounded-tl-sm shadow-inner">
        <div className="flex items-center gap-1.5 py-1 px-1">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
        </div>
      </div>
    </div>
  );
}

function TargetIcon({ size }: { size: number }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
    </svg>
  );
}

function ChatBubble({ from, text }: { from: "ai" | "user", text: string }) {
  const isAi = from === "ai";
  return (
    <div className={cn("flex flex-col max-w-[85%]", isAi ? "mr-auto items-start" : "ml-auto items-end")}>
      <div className="flex items-center gap-1.5 mb-1 px-1">
        {isAi ? (
          <><div className="w-4 h-4 rounded-full bg-indigo-500/20 flex items-center justify-center"><Sparkles size={8} className="text-indigo-400" /></div><span className="text-[9px] font-black uppercase tracking-widest text-slate-500">AI Recruiter</span></>
        ) : (
          <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">You</span>
        )}
      </div>
      <div className={cn("px-4 py-3 rounded-[20px] text-xs font-medium leading-relaxed whitespace-pre-wrap shadow-inner relative", isAi ? "bg-white/[0.04] text-slate-200 border border-white/5 rounded-tl-sm" : "bg-indigo-600 text-white rounded-tr-sm shadow-indigo-500/10")}>
        {text}
      </div>
    </div>
  );
}