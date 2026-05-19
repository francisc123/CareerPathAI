"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import {
  Trophy,
  XCircle,
  ArrowLeft,
  ArrowRight,
  Zap,
  Activity,
  ThumbsUp,
  Target,
  CheckCircle2,
  Lock,
  RotateCcw
} from "lucide-react";
import { cn } from "@/lib/utils";
import { getLearningPath, QuizQuestion } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth.store";

interface QuizItem {
  question: string;
  options: string[];
  correct: number;
}

function parseModuleId(id: string): { week: number; moduleIdx: number } | null {
  const match = id.match(/^w(\d+)-m(\d+)$/);
  if (!match) return null;
  return { week: parseInt(match[1], 10), moduleIdx: parseInt(match[2], 10) };
}

function toQuizItems(quiz: QuizQuestion[]): QuizItem[] {
  return quiz.map((q) => ({
    question: q.question,
    options: q.options,
    correct: q.correct_index,
  }));
}

export default function QuizPage() {
  const [step, setStep] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [answers, setAnswers] = useState<(boolean | null)[]>([]);
  const [isFinished, setIsFinished] = useState(false);
  const [finalScore, setFinalScore] = useState(0);
  const [questions, setQuestions] = useState<QuizItem[]>([]);
  const [moduleTitle, setModuleTitle] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const params = useParams();
  const userId = useAuthStore((s) => s.user?.id);

  const moduleId = (params?.id as string) || "w1-m0";
  const currentQuestion = questions[step];
  const totalQuestions = questions.length;

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const parsed = parseModuleId(moduleId);
      if (!parsed) {
        setError("Invalid module id");
        setLoading(false);
        return;
      }
      if (!userId) {
        setError("Please log in to take this assessment");
        setLoading(false);
        return;
      }
      try {
        const path = await getLearningPath(userId);
        const week = path.weekly_plan?.find((w) => w.week === parsed.week);
        const mod = week?.modules?.[parsed.moduleIdx];
        if (!mod) {
          setError("Module not found in your learning path");
          setLoading(false);
          return;
        }
        const items = toQuizItems(mod.quiz || []);
        if (items.length === 0) {
          setError("No quiz questions generated for this module yet");
          setLoading(false);
          return;
        }
        if (cancelled) return;
        setQuestions(items);
        setAnswers(new Array(items.length).fill(null));
        setModuleTitle(mod.module_title);
      } catch (e: any) {
        if (cancelled) return;
        setError(e?.response?.status === 404 ? "Generate your learning path first" : (e?.message || "Failed to load quiz"));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [moduleId, userId]);

  // Calcul live în timpul testului
  const liveAccuracy = step === 0 ? 100 : Math.round((answers.slice(0, step).filter(a => a === true).length / step) * 100);

  if (loading) {
    return (
      <div className="w-full h-[calc(100vh-210px)] flex items-center justify-center text-xs font-black uppercase tracking-widest text-slate-500">
        Loading assessment...
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-[calc(100vh-210px)] flex items-center justify-center">
        <div className="max-w-md bg-[#0b0f1a]/80 border border-white/5 rounded-[28px] p-8 text-center backdrop-blur-xl">
          <div className="w-14 h-14 rounded-[18px] bg-red-500/10 border border-red-500/20 text-red-400 mx-auto flex items-center justify-center mb-5">
            <XCircle size={22} />
          </div>
          <h2 className="text-lg font-black uppercase tracking-tight text-white mb-2">Cannot start assessment</h2>
          <p className="text-xs text-slate-400 leading-relaxed mb-6">{error}</p>
          <button
            onClick={() => router.push('/learning/path')}
            className="px-6 py-2.5 bg-white text-black rounded-[12px] font-black text-[10px] uppercase tracking-[0.2em] hover:bg-indigo-500 hover:text-white transition-all"
          >
            Back to curriculum
          </button>
        </div>
      </div>
    );
  }

  if (!currentQuestion) {
    return (
      <div className="w-full h-[calc(100vh-210px)] flex items-center justify-center text-xs font-black uppercase tracking-widest text-slate-500">
        No question available
      </div>
    );
  }

  const handleNext = () => {
    const isCorrect = selectedOption === currentQuestion.correct;
    const newAnswers = [...answers];
    newAnswers[step] = isCorrect;
    setAnswers(newAnswers);
    
    if (step < totalQuestions - 1) {
      setStep(s => s + 1);
      setSelectedOption(null);
    } else {
      // Calculăm scorul final real bazat pe noul array completat
      const correctCount = newAnswers.filter(a => a === true).length;
      const calculatedAccuracy = Math.round((correctCount / totalQuestions) * 100);
      setFinalScore(calculatedAccuracy);

      const passed = calculatedAccuracy >= 75;
      
      if (passed) {
        const completed = JSON.parse(localStorage.getItem("completed_modules") || "[]");
        if (!completed.includes(moduleId)) {
          completed.push(moduleId);
          localStorage.setItem("completed_modules", JSON.stringify(completed));
        }
        // Curățăm un eventual cooldown vechi dacă acum a trecut
        const cooldowns = JSON.parse(localStorage.getItem("cooldown_modules") || "{}");
        delete cooldowns[moduleId];
        localStorage.setItem("cooldown_modules", JSON.stringify(cooldowns));
      } else {
        const cooldowns = JSON.parse(localStorage.getItem("cooldown_modules") || "{}");
        cooldowns[moduleId] = Date.now() + (24 * 60 * 60 * 1000); 
        localStorage.setItem("cooldown_modules", JSON.stringify(cooldowns));
      }
      
      setIsFinished(true);
    }
  };

  if (isFinished) {
    const passed = finalScore >= 75;
    
    return (
      <div className="w-full h-[calc(100vh-210px)] flex flex-col items-center justify-center animate-in fade-in duration-500 overflow-hidden">
        <div className="w-full max-w-4xl h-full max-h-[460px] bg-[#0b0f1a]/80 border border-white/[0.08] rounded-[32px] shadow-2xl backdrop-blur-2xl flex flex-col overflow-hidden relative">
          
          <div className="flex justify-between items-center px-6 py-4 border-b border-white/5 bg-white/[0.01] shrink-0">
             <div className="flex items-center gap-2 text-slate-400">
               <Activity size={14} />
               <span className="text-[10px] font-black uppercase tracking-[0.2em]">Module Assessment Finalized</span>
             </div>
             <button onClick={() => router.push('/learning/path')} className="text-[9px] font-black text-slate-500 hover:text-white uppercase tracking-widest transition-colors outline-none">
               Close
             </button>
          </div>

          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 min-h-0">
            <div className="flex flex-col items-center justify-center p-6 border-r border-white/5 relative overflow-hidden">
               <div className={cn(
                 "absolute top-0 w-full h-1/2 blur-[80px] opacity-20 pointer-events-none transition-colors duration-1000",
                 passed ? "bg-emerald-500" : "bg-red-500"
               )} />

               <div className={cn(
                 "w-14 h-14 rounded-[18px] flex items-center justify-center mb-5 border relative z-10 shrink-0",
                 passed ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400" : "bg-red-500/10 border-red-500/20 text-red-400"
               )}>
                 {passed ? <Trophy size={24} /> : <XCircle size={24} />}
               </div>

               <h2 className="text-2xl font-black uppercase tracking-tight text-white mb-2 relative z-10 shrink-0">
                 {passed ? "Qualified" : "Inadequate"}
               </h2>
               <p className="text-[9px] font-bold text-slate-500 uppercase tracking-widest mb-6 relative z-10 shrink-0">
                 {passed ? "Ready for next module" : "System locked for 24H"}
               </p>

               <div className="w-full max-w-[240px] bg-white/[0.02] border border-white/5 rounded-2xl p-3.5 flex justify-around items-center relative z-10 shrink-0">
                 <div className="text-center">
                   <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest mb-1">Final Score</p>
                   <p className={cn("text-xl font-black leading-none", passed ? "text-emerald-400" : "text-red-400")}>{finalScore}%</p>
                 </div>
                 <div className="w-px h-6 bg-white/10" />
                 <div className="text-center">
                   <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest mb-1">Required</p>
                   <p className="text-xl font-black text-white leading-none">75%</p>
                 </div>
               </div>
            </div>

            <div className="flex flex-col justify-between p-6 bg-white/[0.01] min-h-0 overflow-hidden">
              <div className="space-y-4 overflow-y-auto custom-scrollbar pr-2 min-h-0">
                <p className="text-xs font-medium text-slate-300 leading-relaxed">
                  {passed 
                    ? "Excellent performance. Your results have been logged to your Career Readiness profile." 
                    : "Security Protocol: Assessment failed. To ensure genuine learning, this quiz is now on a 24-hour cooldown."}
                </p>
                <div className="space-y-2.5">
                  <div className="flex items-start gap-2.5 bg-white/[0.02] border border-white/5 p-3 rounded-xl">
                    <ThumbsUp size={12} className="text-emerald-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-0.5">Module</p>
                      <p className="text-[11px] font-medium text-slate-300">{moduleTitle || "Assessment completed"}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-2.5 bg-white/[0.02] border border-white/5 p-3 rounded-xl">
                    <Target size={12} className="text-amber-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-0.5">Results</p>
                      <p className="text-[11px] font-medium text-slate-300">
                        {answers.filter(a => a === true).length} of {totalQuestions} answered correctly
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="px-6 py-4 border-t border-white/5 bg-white/[0.01] shrink-0 flex justify-between items-center">
            {passed ? (
              <>
                <button 
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 text-slate-400 hover:text-white flex items-center gap-2 text-[9px] font-black uppercase tracking-widest transition-colors outline-none"
                >
                  <RotateCcw size={12} /> Retake for Practice
                </button>
                <button 
                  onClick={() => router.push('/learning/path')}
                  className="px-6 py-2.5 bg-white text-black hover:bg-indigo-500 hover:text-white rounded-[12px] font-black text-[10px] uppercase tracking-[0.2em] transition-all shadow-xl active:scale-[0.98] outline-none"
                >
                  Return to Curriculum
                </button>
              </>
            ) : (
              <>
                <div className="flex items-center gap-2 text-red-400">
                  <Lock size={14} />
                  <span className="text-[9px] font-black uppercase tracking-widest">Locked for 24h</span>
                </div>
                <button 
                  onClick={() => router.push('/learning/path')}
                  className="px-6 py-2.5 bg-white/10 text-white hover:bg-white/20 rounded-[12px] font-black text-[10px] uppercase tracking-[0.2em] transition-all active:scale-[0.98] outline-none border border-white/5"
                >
                  Review Study Materials
                </button>
              </>
            )}
          </div>

        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-[calc(100vh-210px)] flex flex-col items-center justify-center animate-in fade-in duration-500 overflow-hidden">
      <div className="w-full max-w-4xl h-full max-h-[520px] flex flex-col bg-[#0b0f1a]/80 border border-white/[0.08] rounded-[32px] shadow-2xl backdrop-blur-2xl overflow-hidden">
        
        <div className="flex justify-between items-center px-6 py-4 border-b border-white/5 bg-white/[0.01] shrink-0">
          <button 
            onClick={() => router.back()} 
            className="group flex items-center gap-2 text-[9px] font-black uppercase tracking-[0.3em] text-slate-500 hover:text-red-400 transition-colors outline-none"
          >
            <ArrowLeft size={12} className="group-hover:-translate-x-0.5 transition-transform" /> Quit
          </button>

          <div className="flex items-center gap-4 flex-1 justify-center px-4 md:px-8">
             <div className="flex gap-1 w-full max-w-xs">
                {answers.map((ans, i) => (
                  <div 
                    key={i} 
                    className={cn(
                      "h-1.5 rounded-full transition-all duration-500 flex-1", 
                      i === step ? "bg-white shadow-[0_0_8px_#ffffff]" : ans === true ? "bg-emerald-500" : ans === false ? "bg-red-500" : "bg-white/10"
                    )} 
                  />
                ))}
             </div>
          </div>

          <div className="text-right shrink-0 flex items-center gap-3">
             <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest hidden sm:block">Accuracy</p>
             <p className="text-sm font-black text-white">{liveAccuracy}%</p>
          </div>
        </div>

        <div className="flex-1 flex flex-col items-center justify-center p-6 min-h-0 overflow-y-auto custom-scrollbar">
          <div className="text-center space-y-3 max-w-2xl mb-8 shrink-0">
             <div className="inline-flex items-center justify-center w-10 h-10 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-1 shadow-inner">
               <Zap size={14} className="fill-current animate-pulse" />
             </div>
             <h2 className="text-xl md:text-2xl font-black text-white uppercase tracking-tight leading-snug">
               {currentQuestion.question}
             </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-3xl shrink-0">
            {currentQuestion.options.map((option, idx) => (
              <button 
                key={idx} 
                onClick={() => setSelectedOption(idx)}
                className={cn(
                  "group relative p-4 rounded-[16px] border text-left transition-all duration-200 active:scale-[0.99] outline-none",
                  selectedOption === idx 
                    ? "bg-indigo-600 border-indigo-400 text-white shadow-[0_0_20px_rgba(79,70,229,0.2)]" 
                    : "bg-white/[0.02] border-white/5 text-slate-300 hover:border-white/20 hover:bg-white/[0.04]"
                )}
              >
                <div className="flex items-center justify-between gap-4">
                  <span className="text-xs font-bold tracking-wide leading-tight">{option}</span>
                  <div className={cn(
                    "w-4 h-4 rounded-full border flex items-center justify-center transition-all shrink-0",
                    selectedOption === idx ? "bg-white border-white text-indigo-600" : "border-white/10 text-transparent"
                  )}>
                    <CheckCircle2 size={10} />
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="px-6 py-4 border-t border-white/5 bg-white/[0.01] shrink-0 flex justify-between items-center">
          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">
             Question {step + 1} of {totalQuestions}
          </p>
          
          <button 
            disabled={selectedOption === null}
            onClick={handleNext}
            className="group px-6 py-3 bg-white text-black rounded-[14px] font-black text-[10px] uppercase tracking-[0.2em] hover:bg-indigo-500 hover:text-white transition-all disabled:opacity-10 disabled:cursor-not-allowed flex items-center gap-2 active:scale-95 shadow-xl outline-none"
          >
            {step === totalQuestions - 1 ? "Submit" : "Next"}
            <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform" />
          </button>
        </div>

      </div>
    </div>
  );
}