"use client";

import React, { useState, useEffect } from "react";
import { Search, Filter, ArrowUpDown, ClipboardCheck, ExternalLink, FileText, Briefcase, X } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const MOCK_JOBS = [
  { id: "1", title: "Frontend Developer", company: "Nexus Tech", source: "LinkedIn", match: 94, url: "https://linkedin.com", location: "Remote", coverLetter: "Dear Nexus Tech Team, as a Frontend Developer with 3 years of experience in React..." },
  { id: "2", title: "React Specialist", company: "Innovate Solutions", source: "eJobs", match: 88, url: "https://ejobs.ro", location: "Bucharest", coverLetter: "To the Innovate Solutions HR, I am writing to express my interest in the React Specialist role..." },
  { id: "3", title: "Full Stack Engineer", company: "Cyberdyne", source: "Indeed", match: 72, url: "https://indeed.com", location: "Cluj", coverLetter: "Dear Cyberdyne, my background in both Node.js and React makes me a perfect fit..." },
];

export default function JobsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterSource, setFilterSource] = useState("All");
  const [sortBy, setSortBy] = useState("match");
  const [selectedCoverLetter, setSelectedCoverLetter] = useState<string | null>(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setJobs(MOCK_JOBS);
      setLoading(false);
    }, 1500);
    return () => clearTimeout(timer);
  }, []);

  const filteredJobs = jobs
    .filter(j => filterSource === "All" || j.source === filterSource)
    .sort((a, b) => sortBy === "match" ? b.match - a.match : a.title.localeCompare(b.title));

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-10">
      {/* HEADER & FILTERS */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <h1 className="text-3xl font-black uppercase tracking-tighter text-white">Job Matches</h1>
          <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em]">AI-Powered Career Intelligence</p>
        </div>

        <div className="flex items-center gap-3 bg-white/[0.02] border border-white/10 p-1.5 rounded-2xl backdrop-blur-xl">
          <div className="flex items-center gap-2 px-3 border-r border-white/10">
            <Filter size={14} className="text-indigo-400" />
            <select 
              className="bg-transparent text-[10px] font-bold uppercase tracking-widest outline-none cursor-pointer text-slate-300"
              onChange={(e) => setFilterSource(e.target.value)}
            >
              <option value="All" className="bg-[#020617]">All Sources</option>
              <option value="LinkedIn" className="bg-[#020617]">LinkedIn</option>
              <option value="Indeed" className="bg-[#020617]">Indeed</option>
              <option value="eJobs" className="bg-[#020617]">eJobs</option>
            </select>
          </div>
          <div className="flex items-center gap-2 px-3">
            <ArrowUpDown size={14} className="text-indigo-400" />
            <select 
              className="bg-transparent text-[10px] font-bold uppercase tracking-widest outline-none cursor-pointer text-slate-300"
              onChange={(e) => setSortBy(e.target.value)}
            >
              <option value="match" className="bg-[#020617]">Best Match</option>
              <option value="title" className="bg-[#020617]">Job Title</option>
            </select>
          </div>
        </div>
      </div>

      {/* CONTENT AREA */}
      {loading ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {[1, 2, 3, 4].map(i => <JobSkeleton key={i} />)}
        </div>
      ) : filteredJobs.length > 0 ? (
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
          {filteredJobs.map(job => (
            <JobCard 
              key={job.id} 
              job={job} 
              onViewLetter={() => setSelectedCoverLetter(job.coverLetter)} 
            />
          ))}
        </div>
      ) : (
        <EmptyState />
      )}

      {/* COVER LETTER MODAL */}
      {selectedCoverLetter && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-[#020617]/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="max-w-2xl w-full bg-[#0b0f1a] border border-white/10 rounded-[40px] shadow-2xl overflow-hidden flex flex-col max-h-[80vh]">
            <div className="p-8 border-b border-white/5 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400">
                  <FileText size={20} />
                </div>
                <h2 className="text-xl font-bold uppercase tracking-tight text-white">AI Cover Letter</h2>
              </div>
              <button onClick={() => setSelectedCoverLetter(null)} className="p-2 bg-white/5 rounded-full text-slate-500 hover:text-white transition-colors">
                <X size={18} />
              </button>
            </div>
            <div className="p-8 overflow-y-auto custom-scrollbar bg-white/[0.01]">
              <p className="text-slate-400 text-sm leading-relaxed whitespace-pre-wrap font-mono tracking-tight">
                {selectedCoverLetter}
              </p>
            </div>
            <div className="p-6 bg-[#0b0f1a] border-t border-white/5 flex gap-4">
              <button 
                onClick={() => copyToClipboard(selectedCoverLetter)}
                className="flex-1 py-4 bg-white text-black rounded-2xl font-black text-[10px] uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-all flex items-center justify-center gap-2"
              >
                <ClipboardCheck size={14} /> Copy to Clipboard
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function JobCard({ job, onViewLetter }: { job: any, onViewLetter: () => void }) {
  return (
    <div className="group bg-white/[0.02] border border-white/5 p-6 rounded-[32px] hover:bg-white/[0.04] hover:border-white/10 transition-all flex flex-col justify-between gap-6 shadow-xl backdrop-blur-sm">
      <div className="flex items-start justify-between">
        <div className="flex gap-4">
          <div className="w-12 h-12 rounded-2xl bg-indigo-500/5 border border-white/5 flex items-center justify-center text-indigo-400 shrink-0">
            <Briefcase size={20} />
          </div>
          <div>
            <h3 className="font-bold text-white text-lg leading-tight group-hover:text-indigo-400 transition-colors line-clamp-1">{job.title}</h3>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">{job.company} • {job.location}</p>
          </div>
        </div>
        <div className="flex flex-col items-end shrink-0">
          <div className="px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20">
            <span className="text-[9px] font-black text-indigo-400 uppercase tracking-widest">{job.match}% Match</span>
          </div>
          <span className="text-[8px] font-bold text-slate-600 uppercase tracking-tighter mt-2">{job.source}</span>
        </div>
      </div>

      <div className="flex gap-3">
        <a 
          href={job.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex-1 py-3.5 bg-white text-black rounded-xl font-black text-[9px] uppercase tracking-widest hover:bg-indigo-500 hover:text-white transition-all flex items-center justify-center gap-2"
        >
          Apply <ExternalLink size={12} />
        </a>
        <button 
          onClick={onViewLetter}
          className="px-6 py-3.5 bg-white/[0.03] border border-white/5 text-white rounded-xl font-black text-[9px] uppercase tracking-widest hover:bg-white/10 transition-all flex items-center justify-center gap-2"
        >
          <FileText size={12} /> Cover Letter
        </button>
      </div>
    </div>
  );
}

function JobSkeleton() {
  return (
    <div className="p-6 bg-white/[0.02] border border-white/5 rounded-[32px] space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex gap-4">
          <Skeleton className="h-12 w-12 rounded-2xl" />
          <div className="space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
      <div className="flex gap-3">
        <Skeleton className="h-12 flex-1 rounded-xl" />
        <Skeleton className="h-12 w-32 rounded-xl" />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="h-[400px] flex flex-col items-center justify-center text-center p-10 bg-white/[0.01] border border-dashed border-white/10 rounded-[40px]">
      <div className="w-16 h-16 rounded-3xl bg-indigo-500/5 flex items-center justify-center text-indigo-500/30 mb-6">
        <Search size={32} />
      </div>
      <h3 className="text-xl font-bold text-white uppercase tracking-tight">No Matches Found</h3>
      <p className="text-slate-500 text-xs max-w-xs mt-2 leading-relaxed">
        Your job matches will appear here after CV analysis. Make sure your profile is complete.
      </p>
    </div>
  );
}