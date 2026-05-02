"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import confetti from "canvas-confetti";
import { Trophy, XCircle, ArrowLeft, ArrowRight, Zap, Target, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

const MOCK_QUESTIONS = [
  { id: 1, question: "Which hook is used to handle side effects in functional components?", options: ["useState", "useEffect", "useMemo", "useContext"], correct: 1 },
  { id: 2, question: "What does JSX stand for?", options: ["JavaScript XML", "JSON XML", "Java Syntax Extension", "JavaScript Syntax"], correct: 0 },
  { id: 3, question: "How many elements can a React component return?", options: ["Only one", "Multiple", "Fragmented", "Exactly two"], correct: 2 },
  { id: 4, question: "What is the virtual DOM?", options: ["DOM Copy", "Hardware DOM", "Browser API", "Database"], correct: 0 },
  { id: 5, question: "What is a 'fragment' in React?", options: ["Broken UI", "No-node Wrapper", "State Part", "Style Method"], correct: 1 },
  { id: 6, question: "Default port for local development?", options: ["8080", "5000", "3000", "4200"], correct: 2 },
  { id: 7, question: "Command to create a React app?", options: ["npm create", "npx create", "node install", "npm start"], correct: 1 },
  { id: 8, question: "What is useMemo for?", options: ["Values", "Components", "State", "Routing"], correct: 0 },
  { id: 9, question: "Is React a Framework or a Library?", options: ["Framework", "Library", "Language", "Database"], correct: 1 },
  { id: 10, question: "Who developed React?", options: ["Google", "Twitter", "Facebook", "Microsoft"], correct: 2 },
];

export default function QuizPage() {
  const [step, setStep] = useState(0);
  const [selectedOption, setSelectedOption] = useState<number | null>(null);
  const [answers, setAnswers] = useState<(boolean | null)[]>(new Array(10).fill(null));
  const [isFinished, setIsFinished] = useState(false);
  const [autoFailed, setAutoFailed] = useState(false);
  
  const router = useRouter();
  const currentQuestion = MOCK_QUESTIONS[step];
  const totalQuestions = MOCK_QUESTIONS.length;
  const passingThreshold = 0.75;
  const minCorrectRequired = Math.ceil(totalQuestions * passingThreshold);

  const correctCount = answers.filter(a => a === true).length;
  const mistakesCount = answers.filter(a => a === false).length;
  const accuracy = step === 0 ? 100 : Math.round((correctCount / step) * 100);

  // Auto-Fail Logic
  useEffect(() => {
    const remainingQuestions = totalQuestions - step;
    const maxPossibleCorrect = correctCount + remainingQuestions;

    if (maxPossibleCorrect < minCorrectRequired && !isFinished) {
      setAutoFailed(true);
      setIsFinished(true);
    }
  }, [correctCount, step, totalQuestions, minCorrectRequired, isFinished]);

  const handleNext = () => {
    const isCorrect = selectedOption === currentQuestion.correct;
    const newAnswers = [...answers];
    newAnswers[step] = isCorrect;
    setAnswers(newAnswers);
    
    if (step < totalQuestions - 1) {
      setStep(s => s + 1);
      setSelectedOption(null);
    } else {
      finishQuiz(newAnswers);
    }
  };

  const finishQuiz = (finalAnswers: (boolean | null)[]) => {
    setIsFinished(true);
    const finalCorrect = finalAnswers.filter(a => a === true).length;
    const finalScore = finalCorrect / totalQuestions;
    
    if (finalScore >= passingThreshold) {
      const duration = 3 * 1000;
      const animationEnd = Date.now() + duration;
      const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };
      const randomInRange = (min: number, max: number) => Math.random() * (max - min) + min;

      const interval: any = setInterval(function() {
        const timeLeft = animationEnd - Date.now();
        if (timeLeft <= 0) return clearInterval(interval);
        const particleCount = 50 * (timeLeft / duration);
        
        confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }, colors: ['#6366f1', '#818cf8', '#ffffff'] });
        confetti({ ...defaults, particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }, colors: ['#6366f1', '#10b981', '#ffffff'] });
      }, 250);
    }
  };

  if (isFinished) {
    const passed = (correctCount / totalQuestions) >= passingThreshold;
    
    return (
      /* absolute inset-0 forțează centrarea pe tot spațiul disponibil fără a fi afectat de padding-ul de sus al layout-ului */
      <div className="absolute inset-0 flex items-center justify-center p-4 z-[50]">
        <div className="max-w-md w-full bg-[#020617]/80 border border-white/10 p-8 rounded-[40px] text-center backdrop-blur-3xl shadow-2xl relative overflow-hidden group border-t-white/20">
          
          {/* Accent de fundal mai mic */}
          <div className={cn(
            "absolute -top-20 -left-20 w-48 h-48 blur-[80px] rounded-full opacity-20 transition-colors duration-1000",
            passed ? "bg-emerald-500" : "bg-red-500"
          )} />

          <div className="relative z-10 space-y-6">
            {/* BADGE DESIGN COMPACT */}
            <div className="flex flex-col items-center gap-4">
              <div className={cn(
                "w-20 h-20 rounded-[30px] flex items-center justify-center relative transition-transform duration-500 group-hover:scale-105",
                passed 
                  ? "bg-gradient-to-br from-emerald-500/20 to-emerald-500/5 text-emerald-500 shadow-[0_0_40px_rgba(16,185,129,0.1)]" 
                  : "bg-gradient-to-br from-red-500/20 to-red-500/5 text-red-500 shadow-[0_0_40px_rgba(239,68,68,0.1)]"
              )}>
                {passed ? (
                  <Trophy size={32} strokeWidth={1.5} className="drop-shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
                ) : (
                  <XCircle size={32} strokeWidth={1.5} className="drop-shadow-[0_0_8px_rgba(239,68,68,0.4)]" />
                )}
                <div className="absolute inset-0 rounded-[30px] border border-white/10" />
              </div>
              
              <div className="space-y-1">
                <h2 className="text-3xl font-black uppercase tracking-tighter text-white">
                  {passed ? "Qualified" : "Inadequate"}
                </h2>
                <p className="text-[9px] font-black text-slate-500 uppercase tracking-[0.4em] opacity-80">
                  {autoFailed ? "Threshold unattainable" : "Assessment Complete"}
                </p>
              </div>
            </div>

            {/* STATS COMPACTE - Înălțime redusă */}
            <div className="flex items-center justify-between px-8 py-5 bg-white/[0.02] border border-white/5 rounded-3xl">
              <div className="text-left">
                <p className="text-[7px] font-black text-slate-600 uppercase tracking-widest mb-0.5">Success Rate</p>
                <p className={cn("text-xl font-black", passed ? "text-emerald-400" : "text-white")}>
                  {Math.round((correctCount / totalQuestions) * 100)}%
                </p>
              </div>
              <div className="h-6 w-px bg-white/10" />
              <div className="text-right">
                <p className="text-[7px] font-black text-slate-600 uppercase tracking-widest mb-0.5">Integrity</p>
                <p className="text-xl font-black text-white">{correctCount}/{totalQuestions}</p>
              </div>
            </div>

            <button 
              onClick={() => passed ? router.push('/learning/path') : window.location.reload()} 
              className={cn(
                "w-full py-4 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] transition-all duration-300 active:scale-95 shadow-lg",
                passed 
                  ? "bg-white text-black hover:bg-indigo-500 hover:text-white" 
                  : "bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500 hover:text-white"
              )}
            >
              {passed ? "Proceed to Next Module" : "Re-evaluate Knowledge"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex min-h-0 animate-in fade-in duration-500">
      <div className="flex-1 flex flex-col justify-between py-2 relative">
        <button onClick={() => router.back()} className="absolute top-0 left-0 text-slate-600 hover:text-white transition-all flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.4em]">
          <ArrowLeft size={14} /> Quit Assessment
        </button>

        <div className="space-y-8 max-w-2xl w-full mt-10">
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-indigo-400">
              <Zap size={12} className="fill-current" />
              <span className="text-[9px] font-black uppercase tracking-[0.5em] opacity-60">Intelligence v3.0</span>
            </div>
            <h3 className="text-3xl font-bold text-white leading-tight tracking-tight uppercase">{currentQuestion.question}</h3>
          </div>

          <div className="flex flex-col gap-2.5 w-full">
            {currentQuestion.options.map((option, idx) => (
              <button key={idx} onClick={() => setSelectedOption(idx)} className={cn("w-full px-6 py-3.5 rounded-xl border text-[10px] font-bold uppercase tracking-widest transition-all duration-200 text-left flex items-center justify-between", selectedOption === idx ? "bg-indigo-500/10 text-white border-indigo-500/40 shadow-[0_0_15px_rgba(99,102,241,0.1)]" : "bg-white/[0.02] border-white/5 text-slate-500 hover:text-slate-300 hover:bg-white/[0.04]")}>
                <span>{option}</span>
                <div className={cn("w-1 h-1 rounded-full border transition-all", selectedOption === idx ? "bg-indigo-400 border-indigo-400" : "border-white/10")} />
              </button>
            ))}
          </div>
        </div>

        <div className="max-w-2xl w-full mb-2">
           <p className="text-[8px] font-black text-slate-700 uppercase tracking-[0.5em] mb-3">Session Timeline</p>
           <div className="flex justify-between gap-1 w-full">
              {answers.map((ans, i) => (
                <div key={i} className={cn("h-1 rounded-full transition-all duration-500 flex-1", ans === true ? "bg-emerald-500 shadow-[0_0_10px_#10b981]" : ans === false ? "bg-red-500 shadow-[0_0_10px_#ef4444]" : i === step ? "bg-indigo-500 animate-pulse" : "bg-white/5")} />
              ))}
           </div>
        </div>
      </div>

      <div className="w-64 border-l border-white/5 flex flex-col items-center justify-between py-10 ml-10">
        <div className="text-center space-y-4">
          <p className="text-[9px] font-black text-slate-600 uppercase tracking-[0.5em]">Live Accuracy</p>
          <div className="relative w-32 h-32 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90">
              <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="2" fill="transparent" className="text-white/5" />
              <circle cx="64" cy="64" r="58" stroke="currentColor" strokeWidth="2" fill="transparent" strokeDasharray={364} strokeDashoffset={364 - (364 * accuracy) / 100} className="text-indigo-500 transition-all duration-1000" />
            </svg>
            <div className="absolute flex flex-col items-center leading-none">
              <span className="text-3xl font-black text-white">{accuracy}%</span>
              <Target size={10} className="text-indigo-400 mt-2" />
            </div>
          </div>
        </div>
        <button disabled={selectedOption === null} onClick={handleNext} className="w-20 h-20 rounded-full border border-white/10 bg-white/[0.02] text-white disabled:opacity-10 flex items-center justify-center transition-all hover:bg-indigo-500 hover:border-indigo-400 active:scale-90 group">
          <ArrowRight size={28} className="group-hover:translate-x-1 transition-transform" />
        </button>
        <div className="px-3 py-1.5 rounded-full border border-white/5 bg-white/[0.01]"><p className="text-[8px] font-black text-indigo-400/60 uppercase tracking-[0.2em]">Step {step + 1} of 10</p></div>
      </div>
    </div>
  );
}