"use client";

import React from "react";
import Link from "next/link";
import { Sidebar } from "@/components/sidebar";
import { Globe, Zap, ShieldCheck, UserCircle, LogOut } from "lucide-react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="h-screen w-screen flex flex-col bg-[#020617] text-white overflow-hidden relative font-sans">
      
      {/* --- INJECTARE STIL SCROLLBAR (CUSTOM SLIDE) --- */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 5px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 10px;
          transition: all 0.3s ease;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(99, 102, 241, 0.4);
        }
        /* Firefox */
        .custom-scrollbar {
          scrollbar-width: thin;
          scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
        }
      `}</style>

      {/* Background Decor consistent */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-500/10 blur-[100px]" />
        <div className="absolute bottom-[-5%] right-[-5%] w-[30%] h-[30%] rounded-full bg-blue-500/5 blur-[100px]" />
      </div>

      {/* --- HEADER PREMIUM --- */}
      <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-6 py-6">
        <nav className="w-full max-w-[1440px] flex items-center justify-between px-8 py-3 bg-white/[0.02] border border-white/10 backdrop-blur-xl rounded-full shadow-2xl">
          
          {/* Logo Abstract */}
          <Link href="/" className="flex items-center gap-3 group">
            <div className="relative w-7 h-7">
              <div className="absolute inset-0 bg-indigo-500 rounded-full animate-pulse opacity-20" />
              <div className="absolute inset-0 border-2 border-indigo-400 rounded-full" />
              <div className="absolute inset-0 border-2 border-white/30 rounded-full rotate-45 scale-75" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#fff]" />
            </div>
            <div className="flex flex-col leading-none text-left">
              <span className="text-sm font-black tracking-[0.2em] uppercase text-white">CareerPath</span>
              <span className="text-[9px] text-indigo-400 font-bold tracking-[0.4em] uppercase opacity-80 leading-tight">Intelligence</span>
            </div>
          </Link>

          {/* Navigație Centrată */}
          <div className="hidden md:flex items-center gap-8">
            <NavLink icon={<Globe size={14} />} label="Explore" />
            <NavLink icon={<Zap size={14} />} label="AI Engine" />
            <NavLink icon={<ShieldCheck size={14} />} label="Safety" />
          </div>

          {/* Profil Utilizator */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3 pl-4 border-l border-white/10 group cursor-pointer">
              <div className="text-right hidden sm:block leading-none">
                <p className="text-[10px] font-black text-white uppercase tracking-widest mb-1">ADMIN</p>
                <p className="text-[9px] text-indigo-400 font-bold uppercase tracking-tighter opacity-80">Pro Account</p>
              </div>
              <div className="h-9 w-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 p-[1px] transition-transform group-hover:scale-105">
                <div className="w-full h-full rounded-full bg-[#020617] flex items-center justify-center">
                  <UserCircle size={20} className="text-white/80" />
                </div>
              </div>
            </div>
            
            <button className="p-2 text-slate-500 hover:text-red-400 transition-colors">
              <LogOut size={18} />
            </button>
          </div>
        </nav>
      </header>

      {/* Structură Conținut cu Sidebar */}
      <div className="flex flex-1 overflow-hidden z-10 pt-28">
        <aside className="w-64 hidden lg:block border-r border-white/5 bg-black/10 backdrop-blur-md overflow-hidden">
          <Sidebar />
        </aside>

        {/* --- MAIN AREA CU SCROLLBAR STILIZAT --- */}
        <main className="flex-1 overflow-y-auto custom-scrollbar flex flex-col">
  <div className="max-w-[1400px] mx-auto w-full flex-1 flex flex-col p-10 min-h-0">
    {children}
  </div>
</main>
      </div>
    </div>
  );
}

function NavLink({ icon, label }: { icon: React.ReactNode, label: string }) {
  return (
    <button className="flex items-center gap-2 text-[11px] font-bold uppercase tracking-widest text-slate-500 hover:text-white transition-all group">
      <span className="text-slate-600 group-hover:text-indigo-400 transition-colors">{icon}</span>
      {label}
    </button>
  );
}