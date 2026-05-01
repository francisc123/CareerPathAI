"use client";
import React, { useState, useEffect } from "react";
import { Sidebar } from "@/components/sidebar";
import { ChatPanel } from "@/components/chat-panel";
import { Sparkles, LayoutDashboard, Globe, ShieldCheck, UserCircle, Zap } from "lucide-react";
import Link from "next/link";

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const authStorage = localStorage.getItem("auth-storage");
    if (authStorage) {
      try {
        const { state } = JSON.parse(authStorage);
        setIsAuthenticated(!!state.token);
      } catch {}
    }
  }, []);

  return (
    <div className="h-screen w-screen flex flex-col bg-[#020617] text-white overflow-hidden relative font-sans">
      {/* Background Decor */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-500/10 blur-[100px]" />
        <div className="absolute top-[20%] right-[-5%] w-[30%] h-[30%] rounded-full bg-blue-500/5 blur-[120px]" />
      </div>

      {/* --- PREMIUM HEADER --- */}
      <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-6 py-6">
        <nav className="w-full max-w-[1440px] flex items-center justify-between px-8 py-3 bg-white/[0.02] border border-white/10 backdrop-blur-xl rounded-full shadow-2xl">
          
          {/* ABSTRACT LOGO */}
          <Link href="/" className="flex items-center gap-3 group transition-transform hover:scale-[1.02]">
            <div className="relative w-7 h-7">
              <div className="absolute inset-0 bg-indigo-500 rounded-full mix-blend-screen animate-pulse opacity-20" />
              <div className="absolute inset-0 border-2 border-indigo-400 rounded-full scale-100 group-hover:scale-110 transition-transform duration-500" />
              <div className="absolute inset-0 border-2 border-white/30 rounded-full rotate-45 scale-75 group-hover:rotate-90 transition-transform duration-700" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#fff]" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-sm font-black tracking-[0.2em] uppercase">CareerPath</span>
              <span className="text-[9px] text-indigo-400 font-bold tracking-[0.4em] uppercase opacity-80 leading-tight">Intelligence</span>
            </div>
          </Link>

          {/* Navigation - Center */}
          <div className="hidden md:flex items-center gap-8">
            <NavLink icon={<Globe size={14} />} label="Explore" />
            <NavLink icon={<Zap size={14} />} label="AI Engine" />
            <NavLink icon={<ShieldCheck size={14} />} label="Safety" />
          </div>

          {/* Auth Buttons */}
          <div className="flex items-center gap-3">
            {!isAuthenticated ? (
              <>
                <Link href="/login" className="text-xs font-semibold text-slate-400 hover:text-white transition-colors px-4 py-2">
                  Login
                </Link>
                <Link href="/register" className="relative group">
                  <div className="absolute -inset-2 bg-indigo-500/20 rounded-full blur opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="relative text-xs font-bold bg-white text-black px-6 py-2 rounded-full hover:bg-slate-200 transition-all active:scale-95">
                    Sign Up
                  </span>
                </Link>
              </>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-white/5 border border-white/10 rounded-full group cursor-pointer hover:bg-white/10 transition-all">
                <UserCircle size={18} className="text-indigo-400" />
                <span className="text-xs font-medium text-slate-300">My Account</span>
              </div>
            )}
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden z-10 pt-32">
        <main className="flex-1 flex flex-col lg:flex-row items-center justify-between gap-16 px-12 max-w-[1500px] mx-auto w-full pb-12">
          
          {/* Left Hero Section */}
          <section className="flex-1 space-y-8 animate-in fade-in slide-in-from-left-4 duration-1000">
            <div className="space-y-4">
               <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-bold text-indigo-400 uppercase tracking-widest">
                <Sparkles size={10} /> Powered by AI Agents
              </div>
              <h1 className="text-6xl md:text-[90px] font-bold tracking-tighter leading-[0.95] bg-gradient-to-b from-white to-white/30 bg-clip-text text-transparent">
                Your career,<br />redefined.
              </h1>
            </div>
            <p className="text-lg md:text-xl text-slate-400 font-light max-w-lg leading-relaxed border-l border-white/10 pl-6">
              CV Analysis, smart recommendations, and learning paths. Everything optimized by AI for your success in tech.
            </p>
            <div className="flex gap-4 pt-4">
               {/* Butonul principal trimite acum la Register */}
               <Link href={isAuthenticated ? "/dashboard" : "/register"}>
                 <button className="px-8 py-4 bg-indigo-600 text-white rounded-full text-sm font-bold hover:bg-indigo-500 transition-all shadow-xl shadow-indigo-500/20 active:scale-95">
                  Get Started
                 </button>
               </Link>
               <button className="px-8 py-4 border border-white/10 rounded-full text-sm font-medium hover:bg-white/5 transition-all text-slate-300">
                Project Details
               </button>
            </div>
          </section>

          {/* Right Chat Section */}
          <section className="flex-[1.2] w-full max-w-[550px] h-[500px]"> 
            <div className="h-full bg-white/[0.03] border border-white/10 backdrop-blur-3xl rounded-[40px] overflow-hidden flex flex-col shadow-[0_40px_80px_rgba(0,0,0,0.4)] border-t border-l border-white/20">
              <div className="px-8 py-6 border-b border-white/5 flex items-center justify-between bg-white/[0.01]">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-indigo-500/10 rounded-xl">
                    <Sparkles size={18} className="text-indigo-400" />
                  </div>
                  <span className="text-sm font-bold tracking-widest uppercase text-slate-200">AI Assistant</span>
                </div>
                <div className="flex items-center gap-2">
                   <div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_10px_#10b981]" />
                   <span className="text-[10px] font-bold text-slate-500 tracking-tighter">LIVE</span>
                </div>
              </div>
              <div className="flex-1 overflow-hidden">
                <ChatPanel />
              </div>
            </div>
          </section>

        </main>
      </div>

      {/* Compact Footer */}
      <footer className="h-16 border-t border-white/5 flex items-center justify-center px-6 z-10 bg-[#020617]/50 backdrop-blur-md">
        <p className="text-[11px] text-slate-600 tracking-[0.3em] font-medium uppercase">© 2026 CAREERPATH INTELLIGENCE</p>
      </footer>
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