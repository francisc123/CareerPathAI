"use client";

import React, { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ProgressBar } from "@/components/ui/progress-bar";
import { ModuleCard } from "@/components/ui/module-card";
import { getLearningPath } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth.store";
import { GraduationCap, Zap, Play, ExternalLink } from "lucide-react";

export default function LearningPathPage() {
  const [expandedModule, setExpandedModule] = useState<string | null>(null);
  const [modules, setModules] = useState<any[]>([]);
  const [pathTitle, setPathTitle] = useState("My Learning Path");
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  // Referință pentru a stoca elementele DOM ale fiecărui modul
  const moduleRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  useEffect(() => {
    if (!user?.id) { setLoading(false); return; }
    getLearningPath(user.id)
      .then((path) => {
        setPathTitle(path.title);
        const allModules: any[] = [];
        path.plan_data.forEach((week, wi) => {
          week.modules.forEach((mod, mi) => {
            const id = `w${week.week}-m${mi}`;
            allModules.push({
              id,
              title: mod.module_title,
              week: week.week,
              status: wi === 0 && mi === 0 ? "active" : "locked",
              resources: mod.resources.length,
              resourceList: mod.resources,
            });
          });
        });
        setModules(allModules);
      })
      .catch(() => setModules([]))
      .finally(() => setLoading(false));
  }, [user?.id]);

  // Efect pentru scroll automat când un modul este extins
  useEffect(() => {
    if (expandedModule && moduleRefs.current[expandedModule]) {
      const timeout = setTimeout(() => {
        moduleRefs.current[expandedModule]?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }, 150);
      return () => clearTimeout(timeout);
    }
  }, [expandedModule]);

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-500 pb-20">
      
      {/* HEADER SECTION */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-indigo-400 mb-1">
           <GraduationCap size={14} />
           <span className="text-[10px] font-black uppercase tracking-[0.2em]">Learning Curriculum</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white uppercase">Learning Path</h1>
      </div>

      {/* PROGRESS STAT CARD - REDESIGNED: SLIM & FULL WIDTH */}
      <section className="w-full">
        <div className="bg-white/[0.03] border border-white/5 p-6 rounded-[32px] backdrop-blur-md">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest">Overall Completion</span>
          </div>
          <div className="w-full">
            {/* ProgressBar va ocupa acum 100% din lățimea containerului de p-6 */}
            <ProgressBar progress={modules.length ? Math.round((modules.filter(m => m.status === "completed").length / modules.length) * 100) : 0} />
          </div>
        </div>
      </section>

      {/* MODULES LIST */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-12 bg-white/[0.01] border border-white/5 p-8 rounded-[40px] space-y-8">
          <div className="flex items-center justify-between border-b border-white/5 pb-4">
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-200">
              {loading ? "Loading..." : pathTitle}
            </h2>
          </div>

          <div className="space-y-4">
            {modules.map((mod) => (
              <div
                key={mod.id}
                className="space-y-2 transition-all duration-500"
                ref={(el) => (moduleRefs.current[mod.id] = el)}
              >
                <div
                  onClick={() => mod.status !== "locked" && setExpandedModule(expandedModule === mod.id ? null : mod.id)}
                  className="cursor-pointer"
                >
                  <ModuleCard {...mod} />
                </div>

                {/* EXPANDABLE CONTENT (RESOURCES) */}
                {expandedModule === mod.id && (
                  <div className="mx-6 p-8 bg-white/[0.02] border border-white/5 rounded-b-[32px] animate-in slide-in-from-top-4 duration-300">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                      <div className="space-y-4">
                        <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Study Materials</h4>
                        <div className="space-y-2">
                          {(mod.resourceList || []).map((r: any, i: number) => (
                            <ResourceItem key={i} title={r.title} type={r.type} url={r.url} />
                          ))}
                        </div>
                      </div>
                      <div className="flex flex-col justify-center gap-4">
                        <p className="text-[11px] text-slate-500 italic text-center md:text-left">
                          Complete the resources to unlock the assessment.
                        </p>
                        <button 
                          onClick={() => router.push(`/learning/quiz/${mod.id}`)}
                          className="w-full h-12 bg-white text-black rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] hover:bg-indigo-500 hover:text-white transition-all active:scale-95 flex items-center justify-center gap-2 shadow-xl shadow-white/5"
                        >
                          <Zap size={14} className="fill-current" />
                          Take Module Quiz
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Sub-componentă pentru resurse
function ResourceItem({ title, type, url }: { title: string; type: string; url?: string }) {
  const content = (
    <div className="flex items-center justify-between p-4 rounded-2xl bg-white/5 border border-white/5 hover:border-indigo-500/30 transition-all group cursor-pointer">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white transition-all">
          <Play size={12} className="fill-current" />
        </div>
        <div>
          <p className="text-xs font-bold text-white uppercase tracking-tight">{title}</p>
          <p className="text-[9px] text-slate-500 font-bold uppercase tracking-tighter">{type}</p>
        </div>
      </div>
      <ExternalLink size={14} className="text-slate-600 group-hover:text-white" />
    </div>
  );
  return url ? <a href={url} target="_blank" rel="noopener noreferrer">{content}</a> : content;
}