"use client";
import React from "react";
import { CVScoreGauge } from "@/components/ui/cv-score-gauge";
import { JobCard } from "@/components/ui/job-card";
import { ModuleCard } from "@/components/ui/module-card";
import { ProgressBar } from "@/components/ui/progress-bar";
import { mockDashboardData } from "@/lib/mocks/dashboard";
import { Target, Award, Zap, ArrowRight } from "lucide-react";

export default function DashboardPage() {
  const data = mockDashboardData;

  return (
    <div className="w-full space-y-6 animate-in fade-in duration-500">
      
      {/* HEADER SECTION - Mai compact, aliniat la stânga */}
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2 text-indigo-400 mb-1">
           <Zap size={14} className="fill-current" />
           <span className="text-[10px] font-black uppercase tracking-[0.2em]">System Overview</span>
        </div>
        <h1 className="text-3xl font-bold tracking-tight text-white">Overview</h1>
      </div>

      {/* STATS GRID - 4 carduri mai joase pentru a umple lățimea */}
      <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        {/* CV SCORE - Acum mai compact */}
        <div className="bg-white/[0.03] border border-white/5 p-5 rounded-3xl flex items-center gap-5 backdrop-blur-md">
          <CVScoreGauge score={data.stats.cvScore} size={100} />
          <div>
            <p className="text-2xl font-bold tracking-tighter">{data.stats.cvScore}%</p>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">CV Match</p>
          </div>
        </div>

        {/* LEARNING - Ocupă spațiu pe orizontală */}
        <div className="bg-white/[0.03] border border-white/5 p-5 rounded-3xl flex flex-col justify-center gap-3 backdrop-blur-md">
          <div className="flex justify-between items-center">
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Learning Path</span>
            <span className="text-[10px] text-indigo-400 font-black">{data.stats.learningProgress}%</span>
          </div>
          <ProgressBar progress={data.stats.learningProgress} />
        </div>

        {/* INTERVIEWS */}
        <div className="bg-white/[0.03] border border-white/5 p-5 rounded-3xl flex items-center gap-5 backdrop-blur-md">
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
            <Award size={20} />
          </div>
          <div>
            <p className="text-2xl font-bold tracking-tighter">{data.stats.interviewsCompleted}</p>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Completed</p>
          </div>
        </div>

        {/* CURRENT TARGET / FLOW */}
        <div className="bg-white/[0.03] border border-white/5 p-5 rounded-3xl flex flex-col justify-center backdrop-blur-md">
          <p className="text-[10px] text-indigo-400 font-black uppercase tracking-wider mb-1">Target Role</p>
          <p className="text-sm font-bold text-white truncate">Frontend Developer</p>
        </div>
      </section>

      {/* MAIN CONTENT - Grid strâns (8 col / 4 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* JOBS SECTION - Acum în 2 coloane pentru a umple spațiul */}
        <div className="lg:col-span-8 bg-white/[0.01] border border-white/5 p-6 rounded-[32px] space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-black uppercase tracking-widest text-slate-200">Top Job Matches</h2>
            <button className="flex items-center gap-1 text-[10px] font-bold text-indigo-400 hover:text-white transition-all uppercase">
              View All <ArrowRight size={12} />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.topJobs.map((job) => (
              <JobCard key={job.id} {...job} />
            ))}
          </div>
        </div>

        {/* PATH SECTION - Mai compactă în lateral */}
        <div className="lg:col-span-4 bg-white/[0.01] border border-white/5 p-6 rounded-[32px] space-y-6">
          <h2 className="text-sm font-black uppercase tracking-widest text-slate-200">Learning Path</h2>
          <div className="space-y-3">
            {data.modules.map((mod) => (
              <ModuleCard key={mod.id} {...mod} />
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}