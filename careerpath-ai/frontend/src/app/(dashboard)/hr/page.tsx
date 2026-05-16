"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { 
  MessageSquare, 
  Send, 
  Sparkles, 
  User, 
  StopCircle, 
  Loader2,
  Award,
  Activity,
  ThumbsUp,
  BrainCircuit,
  MessageCircle,
  Lock,
  BookOpen
} from "lucide-react";
import { cn } from "@/lib/utils";

// --- TYPES ---
type WSStatus = "connecting" | "connected" | "disconnected";
type InterviewState = "ongoing" | "completed";

interface ChatMessage {
  from: "ai" | "user";
  text: string;
}

interface HRFeedback {
  communicationScore: number;
  culturalFitScore: number;
  leadershipScore: number;
  overallScore: number;
  strengths: string[];
  areasOfImprovement: string[];
  summary: string;
}

const MAX_TURNS = 15;

export default function HRInterviewPage() {
  // --- MOCK GLOBAL STATE (Aici vei lega Zustand / baza de date în viitor) ---
  // Setat pe true pentru a arăta starea blocată la început
  const [hasPassedQuiz, setHasPassedQuiz] = useState(false); 

  // --- STATE ---
  const [wsStatus, setWsStatus] = useState<WSStatus>("connecting");
  const [interviewState, setInterviewState] = useState<InterviewState>("ongoing");
  const [turnCount, setTurnCount] = useState(1);
  const [sessionId, setSessionId] = useState<string>("");
  
  // Chat State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentAiStream, setCurrentAiStream] = useState("");
  const [isAiStreaming, setIsAiStreaming] = useState(false);
  const [chatInput, setChatInput] = useState("");
  
  // Results State
  const [feedback, setFeedback] = useState<HRFeedback | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // --- INIT & WEBSOCKET ---
  useEffect(() => {
    // Dacă pagina e blocată, nici măcar nu mai inițializăm websocket-ul
    if (!hasPassedQuiz) return; 

    const newSessionId = crypto.randomUUID ? crypto.randomUUID() : `mock-uuid-${Date.now()}`;
    setSessionId(newSessionId);

    setMessages([
      { from: "ai", text: "Hello! I'm your AI HR Interviewer. Today we'll discuss your experience, cultural fit, and soft skills to see how well you align with the company's values. Are you ready to begin?" }
    ]);
  }, [hasPassedQuiz]);

  const connectWS = useCallback(() => {
    if (!sessionId || !hasPassedQuiz) return;

    const token = "mock_jwt_token"; 
    const wsUrl = process.env.NEXT_PUBLIC_HR_WS_URL || `ws://localhost:8000/ws/hr-interview/${sessionId}?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setWsStatus("connected");
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch(data.type) {
          case "delta":
            setIsAiStreaming(true);
            setCurrentAiStream((prev) => prev + data.content);
            break;
            
          case "done":
            setIsAiStreaming(false);
            setMessages((prev) => {
              return [...prev, { from: "ai", text: currentAiStream || data.fullContent || "" }];
            });
            setCurrentAiStream("");
            break;
            
          case "interview_complete":
            setFeedback(data.feedback);
            setInterviewState("completed");
            break;
        }
      } catch (err) {
        console.error("WS Parse error:", err);
      }
    };

    ws.onclose = () => {
      setWsStatus("disconnected");
      setTimeout(connectWS, 5000);
    };
    ws.onerror = () => ws.close();

  }, [sessionId, currentAiStream, hasPassedQuiz]);

  useEffect(() => {
    if (hasPassedQuiz) {
      connectWS();
    }
    return () => wsRef.current?.close();
  }, [connectWS, hasPassedQuiz]);

  // --- AUTO SCROLL ---
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, currentAiStream, isAiStreaming]);

  // --- HANDLERS ---
  const handleSendMessage = () => {
    const text = chatInput.trim();
    if (!text || isAiStreaming) return;
    
    setMessages(prev => [...prev, { from: "user", text }]);
    setChatInput("");
    
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    if (wsRef.current && wsStatus === "connected") {
      wsRef.current.send(JSON.stringify({ type: "chat_message", text }));
      setTurnCount(prev => Math.min(prev + 1, MAX_TURNS));
    } else {
      // --- SIMULARE LOCALĂ ---
      setTurnCount(prev => Math.min(prev + 1, MAX_TURNS));
      setIsAiStreaming(true);
      
      setTimeout(() => {
        if (text.toLowerCase().includes("end") || turnCount >= MAX_TURNS) {
          triggerInterviewComplete();
          return;
        }

        const mockResponse = "That's a very interesting perspective. Can you give me a specific example of a time when you had to deal with a difficult team member to achieve that outcome?";
        let charIndex = 0;
        
        const streamInterval = setInterval(() => {
          if (charIndex < mockResponse.length) {
            setCurrentAiStream((prev) => prev + mockResponse[charIndex]);
            charIndex++;
          } else {
            clearInterval(streamInterval);
            setIsAiStreaming(false);
            setMessages(prev => [...prev, { from: "ai", text: mockResponse }]);
            setCurrentAiStream("");
          }
        }, 30); 

      }, 800); 
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const adjustTextareaHeight = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setChatInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  };

  const triggerInterviewComplete = () => {
    if (wsRef.current && wsStatus === "connected") {
      wsRef.current.send(JSON.stringify({ type: "end_interview" }));
    } else {
      setIsAiStreaming(false);
      setFeedback({
        overallScore: 85,
        communicationScore: 92,
        culturalFitScore: 82,
        leadershipScore: 88,
        summary: "The candidate demonstrated excellent communication skills and a strong sense of accountability. They align well with our core values of transparency and fast-paced delivery, though there is room to grow in adapting to ambiguous structural changes.",
        strengths: [
          "Clear and concise articulation of complex situations",
          "Strong emphasis on team collaboration",
          "Proactive approach to conflict resolution"
        ],
        areasOfImprovement: [
          "Could provide more quantifiable metrics when discussing past achievements",
          "Tendency to over-commit in high-stress scenarios"
        ]
      });
      setInterviewState("completed");
    }
  };


  // ==========================================
  // RENDER 1: LOCKED STATE (Nu a luat nota bună la Quiz-uri)
  // ==========================================
  if (!hasPassedQuiz) {
    return (
      <div className="w-full h-[calc(100vh-210px)] flex flex-col items-center justify-center animate-in zoom-in-95 duration-500">
        <div className="max-w-md w-full bg-[#0b0f1a]/80 border border-white/5 rounded-[40px] p-10 flex flex-col items-center text-center shadow-2xl backdrop-blur-xl relative overflow-hidden">
          
          {/* Decorative Glow */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/10 rounded-full blur-[50px] pointer-events-none" />
          
          <div className="w-20 h-20 rounded-[24px] bg-rose-500/10 flex items-center justify-center text-rose-400 border border-rose-500/20 mb-8 shadow-inner">
            <Lock size={32} />
          </div>
          
          <h2 className="text-2xl font-black uppercase tracking-tight text-white leading-none mb-3">Interview Locked</h2>
          <p className="text-sm font-medium text-slate-400 leading-relaxed mb-8">
            You need to achieve an <strong className="text-indigo-400">80% passing score</strong> in your core learning modules before unlocking the AI Simulation.
          </p>

          <Link 
            href="/learning/path" 
            className="w-full py-4 rounded-[16px] font-black text-xs uppercase tracking-widest transition-all flex items-center justify-center gap-3 bg-white text-black hover:bg-indigo-500 hover:text-white shadow-xl active:scale-95"
          >
            <BookOpen size={16} /> Resume Learning Path
          </Link>

          {/* HIDDEN DEV BUTTON - CA SĂ POȚI TESTA TU */}
          <button 
            onClick={() => setHasPassedQuiz(true)} 
            className="mt-6 text-[9px] font-black text-slate-600 uppercase tracking-widest hover:text-white transition-colors"
          >
            [Dev: Click to Unlock]
          </button>

        </div>
      </div>
    );
  }

  // ==========================================
  // RENDER 2: RESULTS DASHBOARD (ZERO SCROLL FIXED)
  // ==========================================
  if (interviewState === "completed" && feedback) {
    return (
      // Am modificat h-[calc(100vh-140px)] in h-[calc(100vh-210px)] + overflow-hidden
      <div className="w-full h-[calc(100vh-210px)] flex flex-col gap-5 overflow-hidden animate-in zoom-in-95 duration-700">
        
        {/* HEADER COMPACT */}
        <div className="flex items-center gap-4 bg-[#0b0f1a]/60 border border-white/5 rounded-[20px] px-6 py-4 backdrop-blur-xl shrink-0 shadow-lg">
          <div className="w-10 h-10 rounded-[14px] bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20 shrink-0">
            <Award size={20} />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-white uppercase leading-none">Behavioral Assessment Complete</h1>
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1.5">Cultural fit & soft skills evaluated</p>
          </div>
        </div>

        {/* MAIN GRID - Fit to screen (min-h-0) */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-5 min-h-0">
          
          {/* LEFT PANE: Overview & Metrics */}
          <div className="flex flex-col bg-[#0b0f1a]/60 border border-white/5 rounded-[28px] p-6 shadow-2xl backdrop-blur-xl h-full overflow-hidden relative">
            <div className="flex items-center gap-2 text-slate-400 mb-5 shrink-0 border-b border-white/5 pb-4">
              <Activity size={14} />
              <span className="text-[10px] font-black uppercase tracking-widest">Performance Insights</span>
            </div>
            
            {/* Qualitative Metrics */}
            <div className="grid grid-cols-3 gap-3 shrink-0">
              <QualitativeMetric label="Communication" score={feedback.communicationScore} icon={<MessageCircle size={14}/>} />
              <QualitativeMetric label="Cultural Fit" score={feedback.culturalFitScore} icon={<BrainCircuit size={14}/>} />
              <QualitativeMetric label="Leadership" score={feedback.leadershipScore} icon={<User size={14}/>} />
            </div>

            <div className="mt-6 flex flex-col flex-1 min-h-0">
              <h3 className="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-2 shrink-0">Executive Summary</h3>
              {/* Scroll doar pe text daca e prea lung */}
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                <p className="text-[13px] font-medium text-slate-300 leading-relaxed">
                  {feedback.summary}
                </p>
              </div>
            </div>
          </div>

          {/* RIGHT PANE: Strengths & Improvements (Impartit 50/50 vertical) */}
          <div className="flex flex-col gap-5 h-full min-h-0">
            
            {/* Top Half: Strengths */}
            <div className="flex-1 flex flex-col bg-[#0b0f1a]/60 border border-emerald-500/10 rounded-[28px] p-6 shadow-2xl backdrop-blur-xl min-h-0">
              <div className="flex items-center gap-2 text-emerald-400 mb-4 shrink-0">
                <ThumbsUp size={16} />
                <h3 className="text-[10px] font-black uppercase tracking-widest">Key Strengths</h3>
              </div>
              <ul className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-3">
                {feedback.strengths.map((str, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-slate-200">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0 shadow-[0_0_8px_#10b981]" />
                    {str}
                  </li>
                ))}
              </ul>
            </div>

            {/* Bottom Half: Areas for Growth */}
            <div className="flex-1 flex flex-col bg-[#0b0f1a]/60 border border-amber-500/10 rounded-[28px] p-6 shadow-2xl backdrop-blur-xl min-h-0">
              <div className="flex items-center gap-2 text-amber-400 mb-4 shrink-0">
                <TargetIcon size={16} />
                <h3 className="text-[10px] font-black uppercase tracking-widest">Areas for Growth</h3>
              </div>
              <ul className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-3">
                {feedback.areasOfImprovement.map((imp, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-slate-200">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0 shadow-[0_0_8px_#f59e0b]" />
                    {imp}
                  </li>
                ))}
              </ul>
            </div>

          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // RENDER 3: LIVE INTERVIEW UI (Chat Area - ZERO SCROLL)
  // ==========================================
  return (
    <div className="w-full h-[calc(100vh-210px)] flex flex-col gap-5 overflow-hidden animate-in fade-in duration-500">
      
      {/* --- SESSION CONTROL BAR --- */}
      <div className="flex items-center justify-between bg-[#0b0f1a]/60 border border-white/5 rounded-[20px] px-5 py-3 backdrop-blur-xl shrink-0 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-[12px] bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20">
            <MessageSquare size={18} />
          </div>
          <div>
            <h1 className="text-base font-black uppercase tracking-tight text-white leading-none">HR Behavioral Interview</h1>
            <div className="flex items-center gap-1.5 mt-1">
              <div className={cn("w-1.5 h-1.5 rounded-full", wsStatus === "connected" ? "bg-emerald-500 shadow-[0_0_5px_#10b981]" : "bg-amber-500 animate-pulse")} />
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-widest">
                {wsStatus === "connected" ? "Live Session" : "Simulation Mode"}
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end">
            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Progress</span>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-black text-white">Turn {turnCount}</span>
              <span className="text-[10px] font-bold text-slate-500">/ {MAX_TURNS}</span>
            </div>
            <div className="w-24 h-1 bg-white/5 rounded-full mt-1.5 overflow-hidden">
              <div className="h-full bg-indigo-500 rounded-full transition-all duration-500" style={{ width: `${(turnCount / MAX_TURNS) * 100}%` }} />
            </div>
          </div>

          <button 
            onClick={triggerInterviewComplete}
            className="px-5 py-2 rounded-[12px] font-black text-[10px] uppercase tracking-[0.15em] transition-all flex items-center gap-2 text-red-400 bg-red-500/10 hover:bg-red-500 hover:text-white border border-red-500/20 active:scale-95"
          >
            <StopCircle size={12} /> End Interview
          </button>
        </div>
      </div>

      {/* --- MAIN CHAT AREA (Fără Scroll Exterior) --- */}
      <div className="flex-1 flex flex-col bg-[#0b0f1a]/60 border border-white/[0.06] rounded-[28px] overflow-hidden shadow-2xl backdrop-blur-xl min-h-0">
        
        {/* Messages List - Scroll-ul rămâne DOAR aici */}
        <div ref={chatScrollRef} className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-6 min-h-0">
          
          {messages.map((msg, i) => (
            <ChatBubble key={i} from={msg.from} text={msg.text} />
          ))}
          
          {/* Live Streaming Bubble */}
          {isAiStreaming && (
            <ChatBubble from="ai" text={currentAiStream} isStreaming={true} />
          )}

        </div>

        {/* Input Area */}
        <div className="p-4 bg-white/[0.01] border-t border-white/5 shrink-0">
          <div className="relative flex items-end gap-3 bg-[#020617] border border-white/10 focus-within:border-indigo-500/40 rounded-[16px] p-2 transition-all shadow-inner">
            <textarea
              ref={textareaRef}
              value={chatInput}
              onChange={adjustTextareaHeight}
              onKeyDown={handleKeyDown}
              placeholder={isAiStreaming ? "AI is typing..." : "Type your answer... (Shift + Enter for new line)"}
              disabled={isAiStreaming}
              rows={1}
              className="w-full bg-transparent border-none outline-none text-sm font-medium text-white resize-none custom-scrollbar pl-4 py-2 placeholder:text-slate-600 disabled:opacity-50"
            />
            <button 
              onClick={handleSendMessage}
              disabled={!chatInput.trim() || isAiStreaming} 
              className={cn(
                "p-3 rounded-[12px] flex items-center justify-center shrink-0 transition-all duration-300",
                chatInput.trim() && !isAiStreaming
                  ? "bg-indigo-600 text-white shadow-[0_0_15px_rgba(79,70,229,0.4)] hover:bg-indigo-500" 
                  : "bg-white/5 text-slate-500 cursor-not-allowed"
              )}
            >
              <Send size={14} className={cn(chatInput.trim() && !isAiStreaming && "translate-x-0.5 -translate-y-0.5 transition-transform")} />
            </button>
          </div>
          <div className="text-center mt-2.5">
             <span className="text-[9px] font-bold text-slate-600 uppercase tracking-widest">Press Enter to send, Shift+Enter for new line</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// --- UI SUB-COMPONENTS ---

function ChatBubble({ from, text, isStreaming = false }: { from: "ai" | "user", text: string, isStreaming?: boolean }) {
  const isAi = from === "ai";
  
  return (
    <div className={cn("flex flex-col max-w-[85%]", isAi ? "mr-auto items-start" : "ml-auto items-end")}>
      <div className="flex items-center gap-1.5 mb-1 px-1">
        {isAi ? (
          <>
            <div className="w-4 h-4 rounded-full bg-indigo-500/20 flex items-center justify-center">
              <Sparkles size={8} className="text-indigo-400" />
            </div>
            <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">AI Recruiter</span>
          </>
        ) : (
          <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">You</span>
        )}
      </div>
      
      <div className={cn(
        "px-4 py-3 rounded-[20px] text-xs font-medium leading-relaxed whitespace-pre-wrap shadow-inner relative",
        isAi 
          ? "bg-white/[0.04] text-slate-200 border border-white/5 rounded-tl-sm" 
          : "bg-indigo-600 text-white rounded-tr-sm shadow-indigo-500/10"
      )}>
        {text}
        
        {isStreaming && text.length === 0 && (
          <div className="flex items-center gap-1.5 py-1 px-1">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
          </div>
        )}
        {isStreaming && text.length > 0 && (
          <span className="inline-block w-1.5 h-4 bg-indigo-400 ml-1 translate-y-1 animate-pulse" />
        )}
      </div>
    </div>
  );
}

function QualitativeMetric({ label, score, icon }: { label: string, score: number, icon: React.ReactNode }) {
  const getLevel = (s: number) => {
    if (s >= 90) return { text: "Exceptional", color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" };
    if (s >= 80) return { text: "Strong", color: "text-indigo-400", bg: "bg-indigo-500/10 border-indigo-500/20" };
    if (s >= 70) return { text: "Solid", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" };
    return { text: "Developing", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" };
  };

  const level = getLevel(score);

  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-[20px] p-3 flex flex-col items-center justify-center gap-2 group hover:bg-white/[0.04] transition-all duration-300">
      <div className="text-slate-400 bg-white/5 p-2 rounded-full group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>
      <span className="text-[9px] font-black uppercase tracking-widest text-slate-500 text-center">{label}</span>
      <div className={cn("px-3 py-1 rounded-xl border w-full text-center transition-colors duration-300", level.bg)}>
        <span className={cn("text-[9px] font-black uppercase tracking-widest", level.color)}>{level.text}</span>
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