import { BookOpen, Lock, CheckCircle2, Play } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  title: string;
  week: number;
  status: "locked" | "active" | "completed";
  resources: number;
}

export function ModuleCard({ title, week, status, resources }: Props) {
  const isLocked = status === "locked";
  const isCompleted = status === "completed";
  
  return (
    <div className={cn(
      "p-5 rounded-[24px] border transition-all duration-300 relative overflow-hidden group",
      isLocked 
        ? "bg-white/[0.01] border-white/5 opacity-40" 
        : "bg-white/[0.03] border-white/10 hover:border-indigo-500/30 hover:bg-white/[0.05]"
    )}>
      <div className="flex justify-between items-start mb-4">
        <div className="bg-indigo-500/10 px-3 py-1 rounded-full text-[9px] font-black text-indigo-400 border border-indigo-500/20 uppercase tracking-widest">
          Week {week}
        </div>
        {isCompleted && <CheckCircle2 className="text-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.2)]" size={18} />}
        {isLocked && <Lock className="text-slate-600" size={16} />}
      </div>
      
      <h3 className="text-white font-bold text-base mb-1 tracking-tight group-hover:text-indigo-100 transition-colors">
        {title}
      </h3>
      
      <div className="flex items-center gap-2 text-[11px] font-medium text-slate-500 mb-5">
        <BookOpen size={12} />
        <span>{resources} resources</span>
      </div>

      <button 
        disabled={isLocked}
        className={cn(
          "w-full h-10 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all active:scale-[0.98] flex items-center justify-center gap-2",
          isCompleted 
            ? "bg-white/5 text-white border border-white/10 hover:bg-white/10" 
            : isLocked 
              ? "bg-transparent text-slate-600 border border-white/5" 
              : "bg-white text-black hover:bg-slate-200 shadow-xl shadow-white/5"
        )}
      >
        {!isLocked && <Play size={10} className={isCompleted ? "hidden" : "fill-current"} />}
        {isCompleted ? "Review" : isLocked ? "Locked Module" : "Start Now"}
      </button>
    </div>
  );
}