"use client";
import { motion } from "framer-motion";

interface Props {
  progress: number; // 0 - 100
  label?: string;
}

export function ProgressBar({ progress, label }: Props) {
  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between text-xs font-medium text-gray-400 uppercase tracking-wider">
        <span>{label}</span>
        <span>{progress}%</span>
      </div>
      <div className="h-3 w-full bg-gray-800 rounded-full overflow-hidden border border-gray-700">
        <motion.div
          className="h-full bg-primary"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}