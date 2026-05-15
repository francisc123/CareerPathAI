"use client";

import React from "react";
import Link from "next/link";
import { Sidebar } from "@/components/sidebar";
import { Globe, Zap, ShieldCheck, UserCircle } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen w-screen flex flex-col bg-[#020617] text-white overflow-hidden relative font-sans">
      
      {/* Scrollbar Ultra-Thin */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar { width: 3px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.03);
          border-radius: 10px;
        }
      `}</style>

      {/* Glow-uri de fundal unificate */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-5%] w-[45%] h-[45%] rounded-full bg-indigo-500/[0.07] blur-[140px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[35%] h-[35%] rounded-full bg-blue-500/[0.04] blur-[120px]" />
      </div>

      {/* --- HEADER --- */}
      <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-6 py-6 pointer-events-none">
        <nav className="w-full max-w-[1440px] flex items-center justify-between px-8 py-3 bg-white/[0.01] border border-white/5 backdrop-blur-3xl rounded-full shadow-2xl pointer-events-auto">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-7 h-7">
              <div className="absolute inset-0 bg-indigo-500 rounded-full animate-pulse opacity-20" />
              <div className="absolute inset-0 border-2 border-indigo-400 rounded-full" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#fff]" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-sm font-black tracking-[0.2em] uppercase text-white leading-none">CareerPath</span>
              <span className="text-[9px] text-indigo-400 font-bold tracking-[0.4em] uppercase opacity-80 mt-1">Intelligence</span>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <NavLink icon={<Globe size={14} />} label="Explore" />
            <NavLink icon={<Zap size={14} />} label="AI Engine" />
            <NavLink icon={<ShieldCheck size={14} />} label="Safety" />
          </div>

          <div className="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 p-[1px]">
            <div className="w-full h-full rounded-full bg-[#020617] flex items-center justify-center">
              <UserCircle size={20} className="text-white/80" />
            </div>
          </div>
        </nav>
      </header>

      {/* --- ZONA DE CONTINUT (PUSH EFFECT) --- */}
      <div className="flex flex-1 overflow-hidden z-10 pt-28">
        {/* Sidebar integrat cromatic 100% */}
        <Sidebar />

        {/* Main Area - fara bordura, fara padding forțat */}
        <main className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="max-w-[1400px] mx-auto w-full p-10">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

function NavLink({ icon, label }: { icon: React.ReactNode, label: string }) {
  return (
    <button className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-all group">
      <span className="text-slate-600 group-hover:text-indigo-400 transition-colors">{icon}</span>
      {label}
    </button>
  );
}