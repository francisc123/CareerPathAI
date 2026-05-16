"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { GraduationCap, Zap, Play, ExternalLink, ChevronRight, CheckCircle2, Lock, Timer, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

const INITIAL_MODULES = [
  { id: "w1-m0", title: "React Architecture & Performance", week: 1, status: "active", resources: 3, resourceList: [{ title: "Optimization Patterns and techniques", type: "Video", url: "#" }, { title: "Fiber Engine Explained Deep Dive", type: "Article", url: "#" }, { title: "Official Documentation", type: "Docs", url: "#" }] },
  { id: "w1-m1", title: "Global State Management", week: 1, status: "locked", resources: 2, resourceList: [] },
  { id: "w2-m0", title: "Advanced Rendering Patterns", week: 2, status: "locked", resources: 4, resourceList: [] },
];

export default function LearningPathPage() {
  const [expandedModule, setExpandedModule] = useState<string | null>(null);
  const [modules, setModules] = useState(INITIAL_MODULES);
  const [isClient, setIsClient] = useState(false);
  const router = useRouter();

  const syncData = () => {
    const completed = JSON.parse(localStorage.getItem("completed_modules") || "[]");
    const cooldowns = JSON.parse(localStorage.getItem("cooldown_modules") || "{}");
    const now = Date.now();

    const updatedModules = INITIAL_MODULES.map(mod => {
      if (completed.includes(mod.id)) {
        return { ...mod, status: "completed" };
      }
      if (cooldowns[mod.id] && cooldowns[mod.id] > now) {
        return { ...mod, status: "cooldown" };
      }
      return mod;
    });

    if (completed.includes("w1-m0") && updatedModules[1].status === "locked") {
      updatedModules[1].status = "active";
      updatedModules[1].resourceList = [{ title: "Zustand Core Concepts", type: "Video", url: "#" }];
    }

    setModules(updatedModules);
  };

  useEffect(() => {
    setIsClient(true);
    syncData();
  }, []);

  const handleResetStorage = () => {
    localStorage.removeItem("completed_modules");
    localStorage.removeItem("cooldown_modules");
    syncData();
    setExpandedModule(null);
  };

  const completedCount = modules.filter(m => m.status === "completed").length;
  const progressPercent = modules.length ? Math.round((completedCount / modules.length) * 100) : 0;

  if (!isClient) return null;

  return (
    <div className="w-full h-[calc(100vh-170px)] flex flex-col gap-5 overflow-hidden max-w-[1200px] mx-auto min-h-0 p-1">
      
      {/* HEADER SECTION */}
      <div className="flex justify-between items-center shrink-0 bg-[#0b0f1a]/60 border border-white/5 p-5 rounded-[24px] shadow-lg backdrop-blur-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-indigo-400 mb-1">
             <GraduationCap size={16} />
             <span className="text-[10px] font-black uppercase tracking-[0.3em]">Curriculum v2.0</span>
          </div>
          <h1 className="text-2xl font-black tracking-tight text-white uppercase leading-none">Your Growth Path</h1>
        </div>
        
        <div className="flex items-center gap-6 shrink-0">
          <button 
            onClick={handleResetStorage}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/5 bg-white/5 text-[9px] font-black uppercase text-slate-500 hover:text-red-400 hover:border-red-500/20 transition-all outline-none"
          >
            <Trash2 size={10} /> Reset Progress
          </button>

          <div className="flex flex-col items-end gap-1.5">
            <div className="flex items-center gap-2">
               <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Mastery Level</span>
               <span className="text-lg font-black text-white leading-none">{progressPercent}%</span>
            </div>
            <div className="w-40 h-1 bg-white/5 rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-500 rounded-full shadow-[0_0_10px_#6366f1] transition-all duration-1000" 
                style={{ width: `${progressPercent}%` }} 
              />
            </div>
          </div>
        </div>
      </div>

      {/* MODULES FEED */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 pb-4 space-y-4 min-h-0">
        {modules.map((mod, idx) => {
          const isCompleted = mod.status === "completed";
          const isActive = mod.status === "active" || isCompleted || mod.status === "cooldown";
          const isExpanded = expandedModule === mod.id;

          return (
            <div key={mod.id} className="relative group shrink-0">
              <div 
                onClick={() => isActive && setExpandedModule(isExpanded ? null : mod.id)}
                className={cn(
                  "relative z-10 flex flex-col rounded-[28px] border transition-all duration-500 overflow-hidden",
                  isActive 
                    ? "bg-[#0b0f1a]/80 border-white/10 hover:border-indigo-500/20 hover:bg-[#0f1526]/90 shadow-2xl cursor-pointer" 
                    : "bg-transparent border-white/5 opacity-40 cursor-not-allowed"
                )}
              >
                {/* Header-ul cardului */}
                <div className="flex gap-6 p-5 items-center">
                  <div className={cn(
                    "w-11 h-11 rounded-[16px] flex items-center justify-center shrink-0 border transition-all duration-300",
                    isCompleted ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.15)]" :
                    mod.status === "cooldown" ? "bg-red-500/10 border-red-500/20 text-red-400" :
                    isActive ? "bg-indigo-500/10 border-indigo-500/20 text-indigo-400 shadow-[0_0_20px_rgba(99,102,241,0.1)] group-hover:scale-105" : 
                    "bg-white/5 border-white/5 text-slate-600"
                  )}>
                    {isCompleted ? <CheckCircle2 size={20} /> : mod.status === "cooldown" ? <Timer size={18} /> : isActive ? <Zap size={20} className="fill-current" /> : <Lock size={18} />}
                  </div>

                  <div className="flex-1 flex justify-between items-center min-w-0">
                    <div className="min-w-0 pr-4">
                      <p className="text-[9px] font-black uppercase tracking-widest text-slate-500 mb-0.5">Module 0{idx + 1} • Week {mod.week}</p>
                      <h3 className="text-lg font-bold text-white tracking-tight truncate">{mod.title}</h3>
                    </div>
                    {isActive && (
                      <div className="w-9 h-9 rounded-full flex items-center justify-center group-hover:bg-white/5 transition-colors shrink-0">
                        <ChevronRight className={cn("text-slate-400 transition-transform duration-500 ease-out", isExpanded && "rotate-90 text-indigo-400")} />
                      </div>
                    )}
                  </div>
                </div>

                {/* --- PREMIUM CSS GRID EXPANSION ANIMATION --- */}
                <div className={cn(
                  "grid transition-all duration-500 ease-in-out",
                  isExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
                )}>
                  {/* Wrapper necesar pentru a asigura tranzitia corecta de grid-rows */}
                  <div className="overflow-hidden">
                    <div 
                      onClick={(e) => e.stopPropagation()} 
                      className="grid grid-cols-1 md:grid-cols-2 gap-6 px-5 pb-5 pt-4 border-t border-white/5 bg-white/[0.01] cursor-default"
                    >
                      <div className="space-y-3 min-w-0">
                        <h4 className="text-[9px] font-black text-indigo-400 uppercase tracking-widest px-1">Study Materials</h4>
                        <div className="space-y-2">
                          {mod.resourceList.map((res, i) => (
                            <div key={i} className="flex items-center justify-between p-3 rounded-[12px] bg-white/[0.03] border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.06] transition-all cursor-pointer group/item gap-3">
                              <div className="flex items-center gap-3 min-w-0">
                                <Play size={10} className="text-slate-500 group-hover/item:text-indigo-400 transition-colors shrink-0" />
                                <span className="text-xs font-bold text-slate-300 truncate">{res.title}</span>
                              </div>
                              <ExternalLink size={12} className="text-slate-600 group-hover/item:text-white transition-colors shrink-0" />
                            </div>
                          ))}
                        </div>
                      </div>
                      
                      <div className={cn(
                        "flex flex-col justify-end rounded-[20px] p-5 border min-w-0 transition-colors duration-500",
                        isCompleted ? "bg-emerald-500/5 border-emerald-500/10" :
                        mod.status === "cooldown" ? "bg-red-500/5 border-red-500/10" :
                        "bg-indigo-500/5 border-indigo-500/10"
                      )}>
                        <div className={cn(
                          "flex items-center gap-2 mb-2",
                          isCompleted ? "text-emerald-400" : mod.status === "cooldown" ? "text-red-400" : "text-indigo-400"
                        )}>
                          {isCompleted ? <CheckCircle2 size={14} /> : mod.status === "cooldown" ? <Timer size={14} /> : <Zap size={14} className="fill-current" />}
                          <h4 className="text-[9px] font-black uppercase tracking-widest">
                            {isCompleted ? "Assessment Passed" : mod.status === "cooldown" ? "Assessment Locked" : "Module Assessment"}
                          </h4>
                        </div>
                        
                        <p className="text-xs font-medium text-slate-400 mb-4 leading-relaxed">
                          {isCompleted 
                            ? "You have already mastered this module. You can retake the quiz anytime for practice without affecting your score." 
                            : mod.status === "cooldown"
                              ? "This assessment is on a 24-hour cooldown due to a failed attempt. Please review the materials thoroughly before trying again."
                              : "Ready to test your knowledge? Passing this assessment unlocks the next module and prepares you for the AI Interviews."
                          }
                        </p>
                        
                        {mod.status === "cooldown" ? (
                          <button 
                            disabled
                            className="w-full py-3 bg-white/5 text-slate-500 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] cursor-not-allowed flex items-center justify-center gap-2 border border-white/5"
                          >
                            <Lock size={12} /> Unavailable (Cooldown)
                          </button>
                        ) : (
                          <button 
                            onClick={() => router.push(`/learning/quiz/${mod.id}`)}
                            className={cn(
                              "w-full py-3 rounded-xl font-black text-[10px] uppercase tracking-[0.2em] transition-all shadow-xl active:scale-95 flex items-center justify-center gap-2 outline-none",
                              isCompleted 
                                ? "bg-white/[0.05] text-white hover:bg-white/10 border border-white/10" 
                                : "bg-white text-black hover:bg-indigo-500 hover:text-white"
                            )}
                          >
                            {isCompleted ? "Retake for Practice" : "Start Assessment"}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}