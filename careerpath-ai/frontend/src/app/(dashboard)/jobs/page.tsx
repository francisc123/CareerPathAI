"use client";

import React, { useState, useEffect } from "react";
import { Search, Filter, ArrowUpDown, ClipboardCheck, ExternalLink, FileText, Briefcase, X, Sparkles } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { getJobMatches } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth.store";

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterSource, setFilterSource] = useState("All");
  const [sortBy, setSortBy] = useState("match");
  const [selectedCoverLetter, setSelectedCoverLetter] = useState<string | null>(null);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (!user?.id) { setLoading(false); return; }
    getJobMatches(user.id)
      .then(({ matches }) => {
        setJobs(matches.map((m, i) => ({
          id: String(i), title: m.job_title, company: m.company, source: m.source,
          match: m.match_score, url: m.url, location: m.location, coverLetter: m.generated_cover_letter,
        })));
      })
      .catch(() => setJobs([]))
      .finally(() => setLoading(false));
  }, [user?.id]);

  const filteredJobs = jobs
    .filter(j => filterSource === "All" || j.source === filterSource)
    .sort((a, b) => sortBy === "match" ? b.match - a.match : a.title.localeCompare(b.title));

  return (
    <div className="w-full h-[calc(100vh-170px)] flex flex-col gap-6 animate-in fade-in duration-700 overflow-hidden max-w-[1200px] mx-auto min-h-0 p-1">
      
      {/* --- UNIFIED HEADER JOB MATCHES CHENAR --- */}
      <div className="flex justify-between items-center shrink-0 bg-[#0b0f1a]/60 border border-white/5 p-5 rounded-[24px] shadow-lg backdrop-blur-xl">
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-indigo-400 mb-2">
             <Sparkles size={16} />
             <span className="text-[10px] font-black uppercase tracking-[0.3em]">AI-Powered Engines</span>
          </div>
          <h1 className="text-3xl font-black tracking-tight text-white uppercase leading-none">Recommended For You</h1>
        </div>
        
        {/* Filters inline inside the unified header template */}
        <div className="flex items-center gap-3 bg-white/[0.02] border border-white/10 p-1.5 rounded-xl shrink-0">
          <div className="flex items-center gap-2 px-3 border-r border-white/10">
            <Filter size={12} className="text-indigo-400" />
            <select className="bg-transparent text-[9px] font-black uppercase tracking-widest outline-none cursor-pointer text-slate-300" onChange={(e) => setFilterSource(e.target.value)}>
              <option value="All" className="bg-[#020617]">All Sources</option>
              <option value="LinkedIn" className="bg-[#020617]">LinkedIn</option>
              <option value="Indeed" className="bg-[#020617]">Indeed</option>
              <option value="eJobs" className="bg-[#020617]">eJobs</option>
            </select>
          </div>
          <div className="flex items-center gap-2 px-3">
            <ArrowUpDown size={12} className="text-indigo-400" />
            <select className="bg-transparent text-[9px] font-black uppercase tracking-widest outline-none cursor-pointer text-slate-300" onChange={(e) => setSortBy(e.target.value)}>
              <option value="match" className="bg-[#020617]">Best Match</option>
              <option value="title" className="bg-[#020617]">Job Title</option>
            </select>
          </div>
        </div>
      </div>

      {/* CONTENT TRACK - Independent Inner Scroll */}
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 pb-6 min-h-0">
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2, 3, 4].map(i => <JobSkeleton key={i} />)}
          </div>
        ) : filteredJobs.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredJobs.map(job => (
              <JobCard key={job.id} job={job} onViewLetter={() => setSelectedCoverLetter(job.coverLetter)} />
            ))}
          </div>
        ) : (
          <EmptyState />
        )}
      </div>

      {/* COVER LETTER MODAL */}
      {selectedCoverLetter && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-[#020617]/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="max-w-2xl w-full bg-[#0b0f1a] border border-white/10 rounded-[32px] shadow-2xl overflow-hidden flex flex-col max-h-[75vh]">
            <div className="p-6 border-b border-white/5 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400"><FileText size={18} /></div>
                <h2 className="text-lg font-black uppercase tracking-tight text-white">AI Cover Letter</h2>
              </div>
              <button onClick={() => setSelectedCoverLetter(null)} className="p-2 bg-white/5 rounded-full text-slate-500 hover:text-white transition-colors"><X size={16} /></button>
            </div>
            <div className="p-6 overflow-y-auto custom-scrollbar bg-white/[0.01] flex-1 min-h-0">
              <p className="text-slate-400 text-xs leading-relaxed whitespace-pre-wrap font-mono tracking-tight">{selectedCoverLetter}</p>
            </div>
            <div className="p-5 bg-[#0b0f1a] border-t border-white/5 shrink-0">
              <button onClick={() => navigator.clipboard.writeText(selectedCoverLetter)} className="w-full py-3.5 bg-white text-black hover:bg-indigo-500 hover:text-white rounded-xl font-black text-[10px] uppercase tracking-widest transition-colors flex items-center justify-center gap-2"><ClipboardCheck size={12} /> Copy to Clipboard</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function JobCard({ job, onViewLetter }: any) {
  return (
    <div className="group bg-[#0b0f1a]/60 border border-white/5 p-5 rounded-[24px] hover:border-indigo-500/30 transition-all flex flex-col justify-between gap-5 shadow-xl backdrop-blur-sm">
      <div className="flex items-start justify-between min-w-0 gap-4">
        <div className="flex gap-4 min-w-0">
          <div className="w-11 h-11 rounded-[14px] bg-indigo-500/5 border border-white/5 flex items-center justify-center text-indigo-400 shrink-0"><Briefcase size={18} /></div>
          <div className="min-w-0">
            <h3 className="font-bold text-white text-base leading-tight group-hover:text-indigo-400 transition-colors truncate">{job.title}</h3>
            <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest mt-1 truncate">{job.company} • {job.location}</p>
          </div>
        </div>
        <div className="flex flex-col items-end shrink-0">
          <div className="px-2.5 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20"><span className="text-[9px] font-black text-indigo-400 uppercase tracking-widest">{job.match}% Match</span></div>
          <span className="text-[8px] font-bold text-slate-600 uppercase mt-1">{job.source}</span>
        </div>
      </div>
      <div className="flex gap-3 shrink-0">
        <a href={job.url} target="_blank" rel="noopener noreferrer" className="flex-1 py-3 bg-white text-black rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-colors flex items-center justify-center gap-1.5">Apply <ExternalLink size={10} /></a>
        <button onClick={onViewLetter} className="px-4 py-3 bg-white/[0.03] border border-white/5 text-white rounded-xl font-black text-[10px] uppercase tracking-widest hover:bg-white/10 transition-all flex items-center justify-center gap-1.5"><FileText size={10} /> Letter</button>
      </div>
    </div>
  );
}
function JobSkeleton() {
  return (
    <div className="p-5 bg-[#0b0f1a]/40 border border-white/5 rounded-[24px] space-y-4">
      <div className="flex justify-between items-center"><div className="flex gap-4"><Skeleton className="h-11 w-11 rounded-[14px]" /><div className="space-y-1.5"><Skeleton className="h-4 w-32" /><Skeleton className="h-2 w-20" /></div></div><Skeleton className="h-5 w-14 rounded-full" /></div>
      <div className="flex gap-3"><Skeleton className="h-10 flex-1 rounded-xl" /><Skeleton className="h-10 w-24 rounded-xl" /></div>
    </div>
  );
}
function EmptyState() {
  return (
    <div className="h-[300px] flex flex-col items-center justify-center text-center p-8 bg-white/[0.01] border border-dashed border-white/10 rounded-[28px]"><div className="w-12 h-12 rounded-xl bg-indigo-500/5 flex items-center justify-center text-indigo-500/30 mb-4"><Search size={24} /></div><h3 className="text-base font-bold text-white uppercase tracking-tight">No Matches Found</h3><p className="text-slate-500 text-xs max-w-xs mt-1">CV processing complete. Make sure your identity fields are filled.</p></div>
  );
}