"use client";
import { CVScoreGauge } from "@/components/ui/cv-score-gauge";
import { JobCard } from "@/components/ui/job-card";
import { ModuleCard } from "@/components/ui/module-card";
import { ProgressBar } from "@/components/ui/progress-bar";
import { mockDashboardData } from "@/lib/mocks/dashboard";
import { Target, Award, TrendingUp } from "lucide-react";

export default function DashboardPage() {
  const data = mockDashboardData;

  return (
    <div className="max-w-7xl mx-auto space-y-10">
      {/* Rândul de Sus: Statistici */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl flex flex-col items-center shadow-2xl">
          <CVScoreGauge score={data.stats.cvScore} size={110} />
          <p className="text-xs text-gray-400 mt-3 font-medium uppercase tracking-widest">Scor CV</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl flex flex-col justify-center gap-4 shadow-2xl">
          <div className="flex items-center justify-between">
            <Target className="text-primary" size={20} />
            <span className="text-[10px] text-gray-500 font-bold">PROGRES</span>
          </div>
          <ProgressBar progress={data.stats.learningProgress} label="Learning Path" />
        </div>

        <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl flex flex-col items-center justify-center shadow-2xl">
          <Award className="text-amber-500 mb-2" size={32} />
          <p className="text-3xl font-black text-white">{data.stats.interviewsCompleted}</p>
          <p className="text-xs text-gray-400 uppercase tracking-widest mt-1">Interviuri</p>
        </div>

        <div className="bg-gray-900 border border-gray-800 p-6 rounded-2xl flex flex-col justify-center shadow-2xl">
          <div className="flex items-center gap-2 text-green-400 mb-2 text-xs font-bold uppercase">
            <TrendingUp size={14} /> Current Flow
          </div>
          <p className="text-lg font-bold text-white leading-tight">{data.stats.currentFlow}</p>
        </div>
      </section>

      {/* Rândul Central: Jobs & Learning */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
        <div className="lg:col-span-2 space-y-6">
          <h2 className="text-xl font-bold text-white border-l-4 border-primary pl-4">Top Job Matches</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.topJobs.map((job) => (
              <JobCard key={job.id} {...job} />
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <h2 className="text-xl font-bold text-white border-l-4 border-primary pl-4">Learning Path</h2>
          <div className="space-y-4">
            {data.modules.map((mod) => (
              <ModuleCard key={mod.id} {...mod} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}