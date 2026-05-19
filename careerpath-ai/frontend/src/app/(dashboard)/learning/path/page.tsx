"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { GraduationCap, Zap, Play, ExternalLink, ChevronRight, CheckCircle2, Lock, Timer, Trash2, Sparkles, MessageSquare, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { getLearningPath, LearningPath } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth.store";

type ModuleStatus = "active" | "locked" | "completed" | "cooldown";

interface FlatModule {
  id: string;
  title: string;
  description: string;
  week: number;
  status: ModuleStatus;
  resourceList: { title: string; type: string; url: string }[];
}

function flattenPath(path: LearningPath): FlatModule[] {
  const flat: FlatModule[] = [];
  for (const week of path.weekly_plan || []) {
    week.modules.forEach((mod, i) => {
      flat.push({
        id: `w${week.week}-m${i}`,
        title: mod.module_title,
        description: mod.description,
        week: week.week,
        status: "locked",
        resourceList: (mod.resources || []).map((r) => ({
          title: r.title,
          type: r.type,
          url: r.url,
        })),
      });
    });
  }
  return flat;
}

function applyProgress(modules: FlatModule[]): FlatModule[] {
  if (typeof window === "undefined") return modules;
  const completed: string[] = JSON.parse(localStorage.getItem("completed_modules") || "[]");
  const cooldowns: Record<string, number> = JSON.parse(localStorage.getItem("cooldown_modules") || "{}");
  const now = Date.now();

  let nextActiveAssigned = false;
  return modules.map((mod) => {
    if (completed.includes(mod.id)) return { ...mod, status: "completed" as const };
    if (cooldowns[mod.id] && cooldowns[mod.id] > now) return { ...mod, status: "cooldown" as const };
    if (!nextActiveAssigned) {
      nextActiveAssigned = true;
      return { ...mod, status: "active" as const };
    }
    return { ...mod, status: "locked" as const };
  });
}

export default function LearningPathPage() {
  const [expandedModule, setExpandedModule] = useState<string | null>(null);
  const [modules, setModules] = useState<FlatModule[]>([]);
  const [path, setPath] = useState<LearningPath | null>(null);
  const [isClient, setIsClient] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const userId = useAuthStore((s) => s.user?.id);

  const refresh = useCallback(async () => {
    if (!userId) {
      setLoading(false);
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const data = await getLearningPath(userId);
      setPath(data);
      setModules(applyProgress(flattenPath(data)));
    } catch (e: any) {
      const status = e?.response?.status;
      if (status === 404) {
        setError("not_found");
      } else {
        setError(e?.message || "Failed to load learning path");
      }
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    setIsClient(true);
    refresh();
  }, [refresh]);

  // Auto-poll: dacă tocmai a fost încărcat un CV, learning-path-agent generează
  // curriculum-ul async (~20-40s după cv.analyzed). În loc să forțăm refresh
  // manual, retry-uim în liniște la fiecare 5s timp de 90s când suntem pe 404.
  useEffect(() => {
    if (error !== "not_found" || !userId) return;
    const start = Date.now();
    const interval = setInterval(() => {
      if (Date.now() - start > 90_000) {
        clearInterval(interval);
        return;
      }
      refresh();
    }, 5000);
    return () => clearInterval(interval);
  }, [error, userId, refresh]);

  const handleResetStorage = () => {
    localStorage.removeItem("completed_modules");
    localStorage.removeItem("cooldown_modules");
    if (path) setModules(applyProgress(flattenPath(path)));
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
          <h1 className="text-2xl font-black tracking-tight text-white uppercase leading-none">
            {path?.title || "Your Growth Path"}
          </h1>
          {path?.target_role && (
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mt-1">
              Target role: {path.target_role} • {path.estimated_weeks} weeks
            </p>
          )}
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

      {/* LOADING */}
      {loading && (
        <div className="flex-1 flex items-center justify-center min-h-0 text-xs font-black uppercase tracking-widest text-slate-500">
          Loading your curriculum...
        </div>
      )}

      {/* EMPTY / NO PATH YET — distinct copy if a CV was just analyzed */}
      {!loading && (error === "not_found" || (!path && !error)) && (() => {
        const cvRaw = typeof window !== "undefined" ? localStorage.getItem("careerpath_cv_analysis") : null;
        const cv = cvRaw ? JSON.parse(cvRaw) : null;
        const recentlyAnalyzed = cv?.analyzedAt && Date.now() - cv.analyzedAt < 5 * 60 * 1000;
        return (
          <div className="flex-1 flex items-center justify-center min-h-0">
            <div className="max-w-lg w-full bg-[#0b0f1a]/80 border border-white/5 rounded-[28px] p-10 flex flex-col items-center text-center shadow-2xl backdrop-blur-xl">
              <div className="w-16 h-16 rounded-[20px] bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 mb-6 shadow-inner">
                <Sparkles size={26} className={cn(recentlyAnalyzed && "animate-pulse", "fill-current")} />
              </div>
              {recentlyAnalyzed ? (
                <>
                  <h2 className="text-lg font-black uppercase tracking-tight text-white mb-3">Building your curriculum</h2>
                  <p className="text-xs font-medium text-slate-400 leading-relaxed mb-6 max-w-sm">
                    Gemini is generating the weekly plan for <span className="text-indigo-300 font-bold">{cv.targetRole || "your target role"}</span>.
                    This usually takes 20–40s after the CV is analyzed. The page refreshes itself.
                  </p>
                  <div className="w-32 h-1 bg-white/5 rounded-full overflow-hidden mb-4">
                    <div className="h-full w-1/3 bg-indigo-500 rounded-full animate-[pulse_1.5s_ease-in-out_infinite]" />
                  </div>
                  <button
                    onClick={refresh}
                    className="text-[10px] font-black text-slate-500 hover:text-white uppercase tracking-widest transition-colors"
                  >
                    Check now
                  </button>
                </>
              ) : (
                <>
                  <h2 className="text-lg font-black uppercase tracking-tight text-white mb-3">No personalized path yet</h2>
                  <p className="text-xs font-medium text-slate-400 leading-relaxed mb-8 max-w-sm">
                    Upload your CV — once the AI finishes the gap analysis, your personalized week-by-week plan will land here.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-3 w-full">
                    <Link
                      href="/upload"
                      className="flex-1 py-3.5 px-5 rounded-xl bg-white text-black hover:bg-indigo-500 hover:text-white font-black text-[10px] uppercase tracking-[0.15em] flex items-center justify-center gap-2 transition-all active:scale-95"
                    >
                      <MessageSquare size={12} /> Upload CV <ArrowRight size={12} className="opacity-60" />
                    </Link>
                    <Link
                      href="/dashboard"
                      className="flex-1 py-3.5 px-5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white border border-white/10 font-black text-[10px] uppercase tracking-[0.15em] flex items-center justify-center gap-2 transition-all active:scale-95"
                    >
                      Back to dashboard
                    </Link>
                  </div>
                </>
              )}
            </div>
          </div>
        );
      })()}

      {/* GENERIC ERROR */}
      {!loading && error && error !== "not_found" && (
        <div className="flex-1 flex items-center justify-center min-h-0 text-xs font-bold text-red-400">
          Could not load the learning path: {error}
        </div>
      )}

      {/* MODULES FEED */}
      {!loading && !error && path && modules.length > 0 && (
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
                        {mod.description && (
                          <p className="text-[11px] font-medium text-slate-400 leading-relaxed px-1 mb-2">{mod.description}</p>
                        )}
                        <h4 className="text-[9px] font-black text-indigo-400 uppercase tracking-widest px-1">Study Materials</h4>
                        <div className="space-y-2">
                          {mod.resourceList.map((res, i) => (
                            <a
                              key={i}
                              href={res.url || "#"}
                              target="_blank"
                              rel="noreferrer"
                              className="flex items-center justify-between p-3 rounded-[12px] bg-white/[0.03] border border-white/5 hover:border-indigo-500/30 hover:bg-white/[0.06] transition-all cursor-pointer group/item gap-3"
                            >
                              <div className="flex items-center gap-3 min-w-0">
                                <Play size={10} className="text-slate-500 group-hover/item:text-indigo-400 transition-colors shrink-0" />
                                <span className="text-xs font-bold text-slate-300 truncate">{res.title}</span>
                              </div>
                              <ExternalLink size={12} className="text-slate-600 group-hover/item:text-white transition-colors shrink-0" />
                            </a>
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
      )}
    </div>
  );
}