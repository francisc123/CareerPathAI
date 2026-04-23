"use client";
import { motion } from "framer-motion";

interface Props {
  score: number;
  size?: number;
}

export function CVScoreGauge({ score, size = 120 }: Props) {
  const radius = (size - 10) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = (s: number) => {
    if (s < 40) return "#ef4444"; // red-500
    if (s < 70) return "#f59e0b"; // amber-500
    return "#22c55e"; // green-500
  };

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#1f2937" // gray-800
          strokeWidth="8"
          fill="transparent"
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getColor(score)}
          strokeWidth="8"
          fill="transparent"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: offset }}
          transition={{ duration: 1.5, ease: "easeOut" }}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-extrabold text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.3)]">{score}</span>
        <span className="text-[10px] text-gray-300 font-bold uppercase tracking-widest">Match</span>
      </div>
    </div>
  );
}