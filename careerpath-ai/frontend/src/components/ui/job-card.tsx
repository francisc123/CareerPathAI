import { MapPin, Building2, ExternalLink, Sparkles } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";

interface Props {
  title: string;
  company: string;
  location: string;
  source: "LinkedIn" | "Indeed" | "eJobs";
  match: number;
  coverLetter: string;
}

export function JobCard({ title, company, location, source, match, coverLetter }: Props) {
  return (
    <div className="group relative bg-white/[0.02] border border-white/5 hover:border-indigo-500/30 rounded-[28px] p-5 transition-all duration-300 backdrop-blur-md hover:shadow-2xl hover:shadow-indigo-500/10">
      
      {/* HEADER: Source & Match Score */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 shadow-[0_0_8px_#6366f1]" />
          <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 group-hover:text-slate-300 transition-colors">
            {source}
          </span>
        </div>
        <div className="flex items-center gap-1.5 bg-emerald-500/5 px-3 py-1 rounded-full border border-emerald-500/10">
          <Sparkles size={10} className="text-emerald-400" />
          <span className="text-[10px] font-black text-emerald-400 uppercase tracking-tighter">
            {match}% Match
          </span>
        </div>
      </div>

      {/* BODY: Job Info */}
      <div className="space-y-3 mb-6">
        <h3 className="text-base font-bold text-white tracking-tight leading-tight group-hover:text-indigo-100 transition-colors">
          {title}
        </h3>
        <div className="flex flex-wrap gap-x-4 gap-y-2">
          <div className="flex items-center gap-1.5 text-slate-500">
            <Building2 size={13} />
            <span className="text-[11px] font-medium tracking-wide">{company}</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-500">
            <MapPin size={13} />
            <span className="text-[11px] font-medium tracking-wide">{location}</span>
          </div>
        </div>
      </div>

      {/* FOOTER: Actions (No more gray footer bar) */}
      <div className="flex items-center gap-2">
        <Dialog>
          <DialogTrigger asChild>
            <button className="flex-1 h-10 bg-white/5 hover:bg-white/10 border border-white/5 rounded-xl text-[10px] font-black uppercase tracking-[0.1em] text-slate-300 hover:text-white transition-all active:scale-95">
              Draft Cover Letter
            </button>
          </DialogTrigger>
          <DialogContent className="bg-[#020617] text-white border-white/10 rounded-[32px] max-w-2xl backdrop-blur-2xl">
            <DialogHeader>
              <DialogTitle className="text-xl font-bold tracking-tight">AI Generated Letter — {company}</DialogTitle>
            </DialogHeader>
            <div className="mt-4 p-6 bg-white/[0.02] border border-white/5 rounded-2xl text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-medium">
              {coverLetter}
            </div>
          </DialogContent>
        </Dialog>

        <button className="w-10 h-10 flex items-center justify-center bg-indigo-500/10 hover:bg-indigo-500 text-indigo-400 hover:text-white border border-indigo-500/20 rounded-xl transition-all active:scale-95">
          <ExternalLink size={16} />
        </button>
      </div>
    </div>
  );
}