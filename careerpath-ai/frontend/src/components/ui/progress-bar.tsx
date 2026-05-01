"use client";
import { motion } from "framer-motion";

interface Props {
  progress: number;
  label?: string;
}

export function ProgressBar({ progress, label }: Props) {
  return (
    <div className="w-full space-y-3">
      <div className="flex justify-between items-end">
        <span className="text-[10px] font-black text-slate-500 uppercase tracking-[0.2em]">{label}</span>
        <span className="text-xs font-bold text-indigo-400">{progress}%</span>
      </div>
      <div className="h-1.5 w-full bg-white/[0.03] rounded-full overflow-hidden border border-white/5 relative">
        <motion.div
          className="h-full bg-gradient-to-r from-indigo-600 to-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.4)]"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 1.2, ease: "circOut" }}
        />
      </div>
    </div>
  );
}