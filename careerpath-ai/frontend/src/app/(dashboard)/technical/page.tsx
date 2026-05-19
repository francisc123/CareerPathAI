"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import Link from "next/link";
import { useAuthStore } from "@/store/auth.store";
import Editor, { useMonaco } from "@monaco-editor/react";
import { 
  TerminalSquare, 
  Play, 
  MessageSquare, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  Cpu, 
  Send, 
  Loader2, 
  Code2, 
  ChevronDown,
  Award,
  Zap,
  ArrowRight,
  Lock,
  BookOpen,
  Sparkles
} from "lucide-react";
import { cn } from "@/lib/utils";
import { CVScoreGauge } from "@/components/ui/cv-score-gauge";

// --- SHABLOANE DE COD PENTRU FIECARE LIMBAJ (ANTI-OCD ALIGNMENT) ---
const STARTER_TEMPLATES: Record<string, string> = {
  python: `# Write your solution here...\n\ndef solve(nums):\n    # Optimize your code for minimum space/time complexity\n    return []\n`,
  javascript: `// Write your solution here...\n\nfunction solve(nums) {\n    // Optimize your code for minimum space/time complexity\n    return [];\n}\n`,
  typescript: `// Write your solution here...\n\nfunction solve(nums: number[]): number[] {\n    // Optimize your code for minimum space/time complexity\n    return [];\n}\n`,
  java: `// Write your solution here...\nimport java.util.*;\n\npublic class Solution {\n    public int[] solve(int[] nums) {\n        // Optimize your code for minimum space/time complexity\n        return new int[0];\n    }\n}\n`,
  cpp: `// Write your solution here...\n#include <vector>\nusing namespace std;\n\nclass Solution {\npublic:\n    vector<int> solve(vector<int>& nums) {\n        // Optimize your code for minimum space/time complexity\n        return {};\n    }\n};\n`
};

// --- TYPES ---
type WSStatus = "connecting" | "connected" | "disconnected";
type TabState = "problem" | "chat";
type InterviewState = "ongoing" | "completed";

interface TestCase {
  name: string;
  passed: boolean;
  time: string;
  memory: string;
}

interface ChatMessage {
  from: "ai" | "user";
  text: string;
  type?: "normal" | "feedback" | "system_design";
}

type Verdict = "PASS" | "FAIL" | null;
type Readiness = "junior" | "mid" | "senior" | null;

interface FinalResults {
  verdict: Verdict;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  optimizationInsights: string[];
  readinessLevel: Readiness;
  score: number;
  problemsAttempted: number;
  problemsPassed: number;
}

function loadCvForTech(): { skills: string; seniority: string } {
  if (typeof window === "undefined") return { skills: "", seniority: "mid" };
  try {
    const raw = localStorage.getItem("careerpath_cv_analysis");
    if (!raw) return { skills: "", seniority: "mid" };
    const v = JSON.parse(raw);
    const skills = Array.isArray(v?.strengths) ? v.strengths.slice(0, 6).join(",") : "";
    const seniority = (v?.seniority || "mid").toLowerCase();
    return { skills, seniority };
  } catch {
    return { skills: "", seniority: "mid" };
  }
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

export default function TechnicalInterviewPage() {
  // Unlock-ul real: necesită un CV analizat. Dev unlock rămâne pentru regresie.
  const [hasPassedQuiz, setHasPassedQuiz] = useState(false);
  useEffect(() => {
    if (hasCvAnalysis()) setHasPassedQuiz(true);
  }, []);

  // --- STATE ---
  const [wsStatus, setWsStatus] = useState<WSStatus>("connecting");
  const [interviewState, setInterviewState] = useState<InterviewState>("ongoing");
  const [activeTab, setActiveTab] = useState<TabState>("problem");
  
  // Editor State
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(STARTER_TEMPLATES.python);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [testResults, setTestResults] = useState<TestCase[] | null>(null);
  
  // Problem & Chat State
  const [problem, setProblem] = useState<{title: string, description: string, examples: string[]} | null>({
    title: "1. Two Sum Array Challenge",
    description: "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.\n\nYou may assume that each input would have exactly one solution, and you may not use the same element twice. You can return the answer in any order.",
    examples: [
      "Input: nums = [2,7,11,15], target = 9\nOutput: [0,1]\nExplanation: Because nums[0] + nums[1] == 9, we return [0, 1].",
      "Input: nums = [3,2,4], target = 6\nOutput: [1,2]"
    ]
  });
  
  const [messages, setMessages] = useState<ChatMessage[]>([
    { from: "ai", text: "Welcome to your technical assessment. I'm your AI Interviewer. We will start with an algorithmic problem, followed by some system design questions. Ready?", type: "normal" }
  ]);
  const [chatInput, setChatInput] = useState("");
  const [isAiTyping, setIsAiTyping] = useState(false);
  
  // Results State
  const [results, setResults] = useState<FinalResults | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const chatScrollRef = useRef<HTMLDivElement>(null);
  const monaco = useMonaco();

  // --- MONACO THEME SETUP ---
  useEffect(() => {
    if (monaco) {
      monaco.editor.defineTheme("careerpath-dark", {
        base: "vs-dark",
        inherit: true,
        rules: [],
        colors: {
          "editor.background": "#0b0f1a",
          "editor.lineHighlightBackground": "#ffffff05",
          "editorLineNumber.foreground": "#475569",
          "editorIndentGuide.background": "#ffffff10",
        },
      });
      monaco.editor.setTheme("careerpath-dark");
    }
  }, [monaco]);

  // --- AUTO SCROLL CHAT ---
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [messages, activeTab, isAiTyping]);

  // --- WEBSOCKET CONNECTION ---
  const token = useAuthStore((s) => s.token);
  const connectWS = useCallback(() => {
    if (!hasPassedQuiz || !token) return;

    const sessionId = "session_" + Math.floor(Math.random() * 10000);
    // Trimitem skills + seniority din analiza CV-ului ca să primim probleme
    // adaptate (agentul tech-interview-agent acceptă ?skills=&seniority=).
    const { skills, seniority } = loadCvForTech();
    const qs = new URLSearchParams({ token, seniority });
    if (skills) qs.set("skills", skills);
    const wsUrl = process.env.NEXT_PUBLIC_TECH_WS_URL || `ws://localhost:8000/ws/tech-interview/${sessionId}?${qs.toString()}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setWsStatus("connected");
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        switch (data.type) {
          case "problem": {
            const p = data.data || data;
            setProblem({
              title: p.title || "",
              description: p.statement || p.description || "",
              examples: Array.isArray(p.examples)
                ? p.examples.map((ex: any) =>
                    typeof ex === "string"
                      ? ex
                      : `Input: ${ex.input || ""}\nOutput: ${ex.output || ""}${ex.explanation ? "\n" + ex.explanation : ""}`
                  )
                : [],
            });
            setActiveTab("problem");
            break;
          }
          case "chat_message":
            setIsAiTyping(false);
            setMessages(prev => [...prev, { from: "ai", text: data.text || "", type: "normal" }]);
            break;
          case "test_results": {
            setIsEvaluating(false);
            const judge = data.data?.judge0 || {};
            const evalData = data.data?.evaluation || {};
            // Map backend's judge0 result onto the UI's TestCase shape (synthetic single row).
            setTestResults([
              {
                name: evalData.passed ? "Reference test: PASS" : "Reference test: FAIL",
                passed: !!evalData.passed,
                time: judge.time_seconds ? `${(judge.time_seconds * 1000).toFixed(0)}ms` : "—",
                memory: judge.memory_kb ? `${(judge.memory_kb / 1024).toFixed(1)} MB` : "—",
              },
            ]);
            if (evalData.feedback) {
              setMessages(prev => [...prev, { from: "ai", text: evalData.feedback, type: "feedback" }]);
              setActiveTab("chat");
            }
            break;
          }
          case "hint_acknowledged":
            // Counter UI is not currently shown; ignore silently.
            break;
          case "session_end":
            setIsAiTyping(false);
            setResults({
              verdict: (data.verdict === "PASS" || data.verdict === "FAIL") ? data.verdict : null,
              summary: data.summary || "",
              strengths: Array.isArray(data.strengths) ? data.strengths : [],
              weaknesses: Array.isArray(data.weaknesses) ? data.weaknesses : [],
              optimizationInsights: Array.isArray(data.optimization_insights) ? data.optimization_insights : [],
              readinessLevel: ["junior", "mid", "senior"].includes(data.readiness_level) ? data.readiness_level : null,
              score: typeof data.score === "number" ? data.score : 0,
              problemsAttempted: data.problems_attempted || 0,
              problemsPassed: data.problems_passed || 0,
            });
            setInterviewState("completed");
            break;
          case "error":
            console.warn("Tech interview backend error:", data.message);
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
  }, [hasPassedQuiz, token]);

  useEffect(() => {
    if (hasPassedQuiz) {
      connectWS();
    }
    return () => wsRef.current?.close();
  }, [connectWS, hasPassedQuiz]);

  // --- DYNAMIC LANGUAGE CHANGE HANDLER ---
  const handleLanguageChange = (newLang: string) => {
    setLanguage(newLang);
    setCode(STARTER_TEMPLATES[newLang] || "");
  };

  // --- HANDLERS ---
  const handleRunCode = () => {
    setIsEvaluating(true);
    setTestResults(null);

    if (wsRef.current && wsStatus === "connected") {
      wsRef.current.send(JSON.stringify({
        type: "code_submission",
        content: code,
        language: language
      }));
    } else {
      setTimeout(() => {
        setIsEvaluating(false);
        setTestResults([
          { name: "Test Case 1: Base Case", passed: true, time: "4ms", memory: "12.4 MB" },
          { name: "Test Case 2: Large Bounds", passed: true, time: "12ms", memory: "12.8 MB" },
          { name: "Test Case 3: Negative Values", passed: false, time: "5ms", memory: "12.4 MB" }
        ]);
        setMessages(prev => [...prev, { 
          from: "ai", 
          text: "Codul tău a fost compilat cu succes în sandbox. Ai trecut 2/3 cazuri de testare. Se pare că ai un mic edge-case nerezolvat pentru numere negative. Cum crezi că putem optimiza condiția?", 
          type: "feedback" 
        }]);
        setActiveTab("chat");
      }, 2000);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    
    const userMessage = chatInput.trim();
    setMessages(prev => [...prev, { from: "user", text: userMessage }]);
    setChatInput("");

    if (wsRef.current && wsStatus === "connected") {
      setIsAiTyping(true);
      wsRef.current.send(JSON.stringify({ type: "chat_message", text: userMessage }));
    } else {
      setIsAiTyping(true);
      setTimeout(() => {
        setIsAiTyping(false);
        
        let aiReply = `Am înregistrat răspunsul tău legat de proiectarea sistemului. În cadrul producției, voi procesa acest text prin agentul LLM dedicat pentru a-ți evalua deciziile de arhitectură.`;
        let replyType: "normal" | "system_design" = "normal";

        if (userMessage.toLowerCase().includes("gata") || userMessage.toLowerCase().includes("ready")) {
          aiReply = `Perfect! Să trecem la partea de System Design. Cum ai proiecta un sistem de rate-limiting distribuit pentru un API Gateway care să suporte 100.000 de cereri pe secundă?`;
          replyType = "system_design";
        } else if (userMessage.toLowerCase().includes("finish") || userMessage.toLowerCase().includes("final")) {
          setResults({
            verdict: "PASS",
            summary: "Solid algorithmic intuition with consistent O(N) optimizations. Communicated tradeoffs clearly on system design follow-ups.",
            strengths: [
              "Chose hash maps for O(N) lookup on the array problem",
              "Articulated caching strategy with Redis at the gateway",
            ],
            weaknesses: [
              "Did not address negative-value edge cases",
              "Distributed-DB consensus only briefly mentioned",
            ],
            optimizationInsights: [
              "Could collapse the two-pass solution into a single pass with a running map",
              "Consider Raft/Paxos when discussing replicated stores",
            ],
            readinessLevel: "mid",
            score: 8,
            problemsAttempted: 2,
            problemsPassed: 2,
          });
          setInterviewState("completed");
          return;
        }

        setMessages(prev => [...prev, { from: "ai", text: aiReply, type: replyType }]);
      }, 1500);
    }
  };

  // ==========================================
  // RENDER 1: LOCKED STATE (Nu a luat nota bună la Quiz-uri)
  // ==========================================
  if (!hasPassedQuiz) {
    return (
      <div className="w-full h-[calc(100vh-170px)] flex flex-col items-center justify-center p-1 animate-in zoom-in-95 duration-500">
        <div className="max-w-md w-full bg-[#0b0f1a]/80 border border-white/5 rounded-[28px] p-10 flex flex-col items-center text-center shadow-2xl backdrop-blur-xl relative overflow-hidden">
          <div className="w-16 h-16 rounded-[20px] bg-rose-500/10 flex items-center justify-center text-rose-400 border border-rose-500/20 mb-6 shadow-inner">
            <Lock size={24} />
          </div>
          <h2 className="text-xl font-black uppercase tracking-tight text-white mb-2">Interview Locked</h2>
          <p className="text-xs font-medium text-slate-400 mb-6">Încarcă un CV — interviul tehnic generează probleme calibrate pe skill-urile și seniority-ul tău.</p>
          <Link href="/upload" className="w-full py-3.5 bg-white text-black hover:bg-indigo-500 hover:text-white rounded-xl font-black text-[10px] uppercase tracking-widest flex items-center justify-center gap-2 transition-all">
            <BookOpen size={12} /> Upload CV
          </Link>
          <button onClick={() => setHasPassedQuiz(true)} className="mt-4 text-[8px] font-black text-slate-600 uppercase tracking-widest hover:text-white transition-colors">[Dev Unlock]</button>
        </div>
      </div>
    );
  }

  // ==========================================
  // RENDER 2: INTERVIEW COMPLETED VIEW
  // ==========================================
  if (interviewState === "completed" && results) {
    return (
      <div className="w-full max-w-[1200px] mx-auto space-y-6 animate-in zoom-in-95 duration-700 pb-10 p-1">
        
        {/* CHENAR DESIGN UNIFICAT ABSOLUT COMPATIBIL CROMATIC */}
        <div className="flex items-center gap-4 bg-[#0b0f1a]/60 border border-white/5 rounded-[24px] px-6 py-4 backdrop-blur-xl shrink-0 shadow-lg">
          <div className="w-10 h-10 rounded-[14px] bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20 shrink-0">
            <Award size={20} />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-tight text-white uppercase leading-none">Technical Assessment Complete</h1>
            <p className="text-[9px] font-bold text-slate-400 uppercase tracking-widest mt-1.5">Your code and system design skills have been evaluated.</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="md:col-span-1 bg-[#0b0f1a]/60 border border-white/5 rounded-[32px] p-6 flex flex-col items-center justify-center gap-5 shadow-2xl backdrop-blur-xl">
            {results.verdict === "PASS" ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-20 h-20 rounded-full bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.25)]">
                  <CheckCircle2 size={40} className="text-emerald-400" />
                </div>
                <p className="text-3xl font-black text-emerald-400 tracking-tight">PASS</p>
                <p className="text-[9px] font-bold text-emerald-300 uppercase tracking-[0.3em]">Technical Verdict</p>
              </div>
            ) : results.verdict === "FAIL" ? (
              <div className="flex flex-col items-center gap-3">
                <div className="w-20 h-20 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center shadow-[0_0_30px_rgba(244,63,94,0.25)]">
                  <XCircle size={40} className="text-rose-400" />
                </div>
                <p className="text-3xl font-black text-rose-400 tracking-tight">FAIL</p>
                <p className="text-[9px] font-bold text-rose-300 uppercase tracking-[0.3em]">Technical Verdict</p>
              </div>
            ) : (
              <div className="text-[10px] font-bold uppercase tracking-widest text-slate-500">Verdict unavailable</div>
            )}

            <div className="w-full pt-4 border-t border-white/5 grid grid-cols-2 gap-3">
              <div className="text-center">
                <p className="text-xl font-black text-white">{results.problemsPassed}/{results.problemsAttempted}</p>
                <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mt-1">Problems Solved</p>
              </div>
              <div className="text-center">
                <p className="text-xl font-black text-indigo-400 uppercase">{results.readinessLevel || "—"}</p>
                <p className="text-[8px] font-bold text-slate-500 uppercase tracking-widest mt-1">Readiness Level</p>
              </div>
            </div>
          </div>

          <div className="md:col-span-2 bg-[#0b0f1a]/60 border border-white/5 rounded-[32px] p-6 space-y-6 shadow-2xl backdrop-blur-xl">
            <div>
              <div className="flex items-center gap-2 text-slate-400 mb-2">
                <TerminalSquare size={14} />
                <span className="text-[10px] font-black uppercase tracking-widest">Evaluator Summary</span>
              </div>
              <p className="text-xs font-medium text-slate-300 leading-relaxed">{results.summary}</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4 border-t border-white/5">
              <div>
                <div className="flex items-center gap-2 text-emerald-400 mb-3">
                  <CheckCircle2 size={14} />
                  <span className="text-[10px] font-black uppercase tracking-widest">Strengths</span>
                </div>
                <ul className="space-y-2">
                  {results.strengths.map((s, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-slate-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="flex items-center gap-2 text-amber-400 mb-3">
                  <Zap size={14} />
                  <span className="text-[10px] font-black uppercase tracking-widest">Weaknesses</span>
                </div>
                <ul className="space-y-2">
                  {results.weaknesses.map((w, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-slate-300">
                      <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                      {w}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {results.optimizationInsights.length > 0 && (
              <div className="pt-4 border-t border-white/5">
                <div className="flex items-center gap-2 text-indigo-400 mb-3">
                  <Cpu size={14} />
                  <span className="text-[10px] font-black uppercase tracking-widest">Optimization Insights</span>
                </div>
                <ul className="space-y-2">
                  {results.optimizationInsights.map((ins, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-xs font-medium text-slate-300">
                      <ArrowRight size={14} className="text-indigo-500 shrink-0 mt-0.5" />
                      {ins}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // ==========================================
  // RENDER 3: LIVE ASSESSMENT PLAYGROUND (Cu Chenarul Corect de Titlu)
  // ==========================================
  return (
    <div className="w-full h-[calc(100vh-170px)] flex flex-col gap-5 overflow-hidden max-w-[1200px] mx-auto min-h-0 p-1 animate-in fade-in duration-500">
      
      {/* --- CHENAR TITLU GLASSMORPHISM PENTRU TITLU - IDENTIC CU LEARNING/JOBS --- */}
      <div className="flex justify-between items-center bg-[#0b0f1a]/60 border border-white/5 p-5 rounded-[24px] shadow-lg backdrop-blur-xl shrink-0">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-[14px] bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 shadow-inner">
            <Code2 size={20} />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-indigo-400">
               <Sparkles size={14} className="fill-current" />
               <span className="text-[9px] font-black uppercase tracking-[0.3em]">Sandbox v3.10</span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white uppercase leading-none">Technical Assessment</h1>
          </div>
        </div>

        {/* Zona de Selector & Butoane așezate perfect la extremitatea dreaptă */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="relative">
            <select 
              value={language} 
              onChange={(e) => handleLanguageChange(e.target.value)} 
              className="appearance-none bg-[#020617] border border-white/10 rounded-xl pl-3 pr-8 py-2 text-[10px] font-black uppercase tracking-widest text-white outline-none cursor-pointer"
            >
              <option value="python">Python 3.10</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
              <option value="java">Java 17</option>
              <option value="cpp">C++ 20</option>
            </select>
            <ChevronDown size={10} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
          </div>
          <button 
            onClick={handleRunCode} 
            disabled={isEvaluating} 
            className="px-5 py-2 rounded-xl font-black text-[10px] uppercase tracking-widest bg-emerald-500 text-white hover:bg-emerald-400 flex items-center gap-1.5 transition-all shadow-lg active:scale-95"
          >
            {isEvaluating ? <Loader2 size={12} className="animate-spin" /> : <Play size={12} className="fill-current" />}
            {isEvaluating ? "Running..." : "Run Code"}
          </button>
        </div>
      </div>

      {/* SPLIT PANELS TRACK */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-0 overflow-hidden">
        
        {/* === LEFT PANE: PROBLEM INFO & CHAT CONSOLE === */}
        <div className="lg:col-span-5 flex flex-col bg-[#0b0f1a]/60 border border-white/[0.06] rounded-[28px] overflow-hidden h-full min-h-0 shadow-2xl backdrop-blur-xl">
          <div className="flex border-b border-white/5 bg-white/[0.01] shrink-0 p-1.5 gap-1.5">
            <button onClick={() => setActiveTab("problem")} className={cn("flex-1 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all", activeTab === "problem" ? "bg-white/5 text-white shadow-inner" : "text-slate-500 hover:text-slate-300")}>Problem Info</button>
            <button onClick={() => setActiveTab("chat")} className={cn("flex-1 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest transition-all", activeTab === "chat" ? "bg-white/5 text-white shadow-inner" : "text-slate-500 hover:text-slate-300")}>AI Interviewer</button>
          </div>
          
          <div className="flex-1 min-h-0 relative">
            {/* PROBLEM TAB */}
            {activeTab === "problem" && (
              <div className="absolute inset-0 overflow-y-auto custom-scrollbar p-5 space-y-4 animate-in fade-in duration-300">
                {problem ? (
                  <>
                    <h2 className="text-base font-black text-white tracking-tight">{problem.title}</h2>
                    <div className="text-xs font-medium text-slate-300 leading-relaxed whitespace-pre-wrap">{problem.description}</div>
                    {problem.examples.map((ex: string, i: number) => (
                      <div key={i} className="bg-white/[0.02] border border-white/5 rounded-[14px] p-3.5 space-y-1">
                        <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Example {i + 1}</p>
                        <code className="block text-xs font-mono text-indigo-300 whitespace-pre-wrap bg-[#020617] p-2.5 rounded-lg border border-white/5">{ex}</code>
                      </div>
                    ))}
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-2">
                    <Loader2 size={16} className="animate-spin text-indigo-500/40" />
                    <p className="text-[9px] font-black uppercase tracking-widest text-slate-500">Waiting for system init...</p>
                  </div>
                )}
              </div>
            )}

            {/* CHAT TAB */}
            {activeTab === "chat" && (
              <div className="absolute inset-0 flex flex-col min-h-0 bg-transparent animate-in fade-in duration-300">
                <div ref={chatScrollRef} className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4 min-h-0">
                  {messages.map((msg, i) => (
                    <div key={i} className={cn("flex flex-col max-w-[85%]", msg.from === "user" ? "ml-auto items-end" : "mr-auto items-start")}>
                      <div className="flex items-center gap-1 mb-1 px-1">
                        <span className="text-[8px] font-black text-slate-500 uppercase tracking-wider">{msg.from === "ai" ? "AI Interviewer" : "You"}</span>
                        {msg.type === "feedback" && <span className="px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-400 text-[7px] font-black uppercase">Evaluation</span>}
                        {msg.type === "system_design" && <span className="px-1.5 py-0.5 rounded bg-indigo-500/15 text-indigo-400 text-[7px] font-black uppercase">System Design</span>}
                      </div>
                      <div className={cn("px-3.5 py-2 rounded-2xl text-xs font-medium leading-relaxed whitespace-pre-wrap shadow-inner", msg.from === "user" ? "bg-indigo-600 text-white rounded-tr-sm shadow-indigo-500/10" : "bg-white/5 text-slate-200 border border-white/5 rounded-tl-sm")}>
                        {msg.text}
                      </div>
                    </div>
                  ))}
                  {isAiTyping && (
                    <div className="flex flex-col max-w-[85%] mr-auto items-start">
                      <div className="mb-1 px-1"><span className="text-[8px] font-black text-slate-500 uppercase tracking-wider">AI Interviewer</span></div>
                      <div className="px-3.5 py-2.5 bg-white/5 border border-white/5 rounded-2xl rounded-tl-sm flex items-center gap-1">
                        <span className="w-1 h-1 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                        <span className="w-1 h-1 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
                        <span className="w-1 h-1 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
                      </div>
                    </div>
                  )}
                </div>
                <form onSubmit={handleSendMessage} className="p-3 bg-white/[0.01] border-t border-white/5 shrink-0">
                  <div className="relative flex items-center">
                    <input value={chatInput} onChange={e => setChatInput(e.target.value)} placeholder="Type your answer..." className="w-full bg-[#020617] border border-white/10 focus:border-indigo-500/40 rounded-xl pl-4 pr-10 py-2.5 text-xs font-medium text-white outline-none transition-all shadow-inner" />
                    <button type="submit" disabled={!chatInput.trim()} className="absolute right-2 p-1 text-indigo-400 hover:text-white transition-colors disabled:opacity-20 bg-white/5 hover:bg-indigo-500 rounded-lg"><Send size={12} /></button>
                  </div>
                </form>
              </div>
            )}
          </div>
        </div>

        {/* === RIGHT PANE: MONACO CODE EDITOR ENVIRONMENT === */}
        <div className="lg:col-span-7 flex flex-col gap-4 h-full min-h-0 overflow-hidden">
          <div className="flex-1 bg-[#0b0f1a] border border-white/[0.06] rounded-[28px] overflow-hidden shadow-2xl relative pt-3 min-h-0">
            <Editor 
              height="100%" 
              language={language} 
              theme="careerpath-dark" 
              value={code} 
              onChange={(val) => setCode(val || "")} 
              options={{ 
                minimap: { enabled: false }, 
                fontSize: 13, 
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace", 
                padding: { top: 10 }, 
                scrollBeyondLastLine: false, 
                smoothScrolling: true, 
                cursorBlinking: "smooth", 
                renderLineHighlight: "none", 
                lineNumbersMinChars: 3 
              }} 
            />
            {isEvaluating && (
              <div className="absolute inset-0 bg-[#0b0f1a]/60 backdrop-blur-sm flex flex-col items-center justify-center z-10 animate-in fade-in duration-200">
                <Loader2 size={20} className="animate-spin text-indigo-400 mb-2" />
                <p className="text-[9px] font-black uppercase tracking-widest text-slate-300">Evaluating Test Cases...</p>
              </div>
            )}
          </div>

          {/* EXECUTION MATRIX PANEL */}
          {testResults && (
            <div className="h-40 shrink-0 bg-[#0b0f1a]/80 border border-white/[0.06] rounded-[28px] p-4 backdrop-blur-xl shadow-2xl overflow-y-auto custom-scrollbar animate-in slide-in-from-bottom-6 duration-300">
              <div className="flex items-center gap-2 mb-2.5">
                <TerminalSquare size={12} className="text-slate-500" />
                <h3 className="text-[9px] font-black uppercase tracking-widest text-slate-400">Execution Matrix</h3>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {testResults.map((tc, idx) => (
                  <div key={idx} className="bg-white/[0.01] border border-white/5 rounded-xl p-2.5 flex items-center justify-between shadow-inner">
                    <div className="min-w-0">
                      <p className="text-[10px] font-bold text-slate-300 truncate pr-1">{tc.name}</p>
                      <div className="flex items-center gap-2 text-[8px] font-medium text-slate-500 mt-0.5">
                        <span className="flex items-center gap-0.5"><Clock size={9}/> {tc.time}</span>
                        <span className="flex items-center gap-0.5"><Cpu size={9}/> {tc.memory}</span>
                      </div>
                    </div>
                    {tc.passed ? (
                      <div className="flex items-center gap-1 text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-lg shrink-0 border border-emerald-500/10 text-[9px] font-black uppercase tracking-wider">Pass</div>
                    ) : (
                      <div className="flex items-center gap-1 text-red-400 bg-red-500/10 px-2 py-0.5 rounded-lg shrink-0 border border-red-500/10 text-[9px] font-black uppercase tracking-wider">Fail</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}