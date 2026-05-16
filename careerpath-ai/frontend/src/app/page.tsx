"use client";

import React, { useState, useEffect } from "react";
import { ChatPanel } from "@/components/chat-panel";
import { 
  Sparkles, 
  Globe, 
  ShieldCheck, 
  UserCircle, 
  Zap, 
  Briefcase, 
  Cpu, 
  CheckCircle2, 
  ArrowRight,
  Shield,
  Layers,
  Terminal
} from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

// --- SUBSCRIPTION DATA MAPPING ---
const PRICING_PLANS = [
  {
    name: "Standard Loop",
    price: "0",
    period: "forever",
    desc: "Perfect for discovering your current market baseline index.",
    features: [
      "1 CV Analysis & Readiness Score", 
      "Access to Week 1 Core Curriculum", 
      "Standard AI Assistant Chat"
    ],
    cta: "Start Free Loop",
    premium: false
  },
  {
    name: "Professional Agent",
    price: "19",
    period: "month",
    desc: "Unlocks the complete automated behavioral & technical compiler matrix.",
    features: [
      "Unlimited CV Parsing & Score Tracking", 
      "Full Curriculum Path Access (All Weeks)", 
      "Unlimited LLM HR & Technical Simulations", 
      "Zero Cooldown on Quiz Re-evaluations"
    ],
    cta: "Upgrade to Professional",
    premium: true
  },
  {
    name: "Corporate Enterprise",
    price: "99",
    period: "month",
    desc: "Tailored vectors for high-growth technical engineering teams.",
    features: [
      "Custom Candidate Benchmarking Profiles", 
      "Dedicated LLM Interview Sandbox Rules", 
      "Team Performance Telemetry Reports", 
      "Priority API Access Protocols"
    ],
    cta: "Contact Architecture",
    premium: false
  }
];

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
    // SETAT PE snap-proximity: Magnetism fin doar când ești foarte aproape de secțiune
    <div className="h-screen w-screen overflow-y-auto snap-y snap-proximity scroll-smooth bg-[#020617] text-white relative font-sans custom-scrollbar">
      
      {/* Glow-uri de fundal unificate și discrete */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/[0.05] blur-[140px]" />
        <div className="absolute bottom-[-5%] right-[-5%] w-[40%] h-[40%] rounded-full bg-blue-500/[0.03] blur-[120px]" />
      </div>

      {/* ==========================================
          --- FIXED NAVIGATION HEADER ---
          ========================================== */}
      <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-6 py-6 pointer-events-none">
        <nav className="w-full max-w-[1440px] flex items-center justify-between px-8 py-3 bg-[#020617]/40 border border-white/5 backdrop-blur-3xl rounded-full shadow-2xl pointer-events-auto">
          
          <Link href="/" className="flex items-center gap-3 group transition-transform hover:scale-[1.01]">
            <div className="relative w-7 h-7">
              <div className="absolute inset-0 bg-indigo-500 rounded-full animate-pulse opacity-20" />
              <div className="absolute inset-0 border-2 border-indigo-400 rounded-full scale-100 group-hover:scale-105 transition-transform duration-500" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#fff]" />
            </div>
            <div className="flex flex-col leading-none">
              <span className="text-sm font-black tracking-[0.2em] uppercase">CareerPath</span>
              <span className="text-[9px] text-indigo-400 font-bold tracking-[0.4em] uppercase opacity-80 mt-1">Intelligence</span>
            </div>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors">Why Us</a>
            <a href="#process" className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors">The Process</a>
            <a href="#pricing" className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors">Pricing</a>
          </div>

          <div className="flex items-center gap-3">
            {!isAuthenticated ? (
              <>
                <Link href="/login" className="text-xs font-bold text-slate-400 hover:text-white transition-colors px-4 py-2">
                  Login
                </Link>
                <Link href="/register" className="relative group">
                  <span className="relative text-xs font-black uppercase tracking-wider bg-white text-black px-6 py-2.5 rounded-full hover:bg-slate-200 transition-all active:scale-95 block">
                    Sign Up
                  </span>
                </Link>
              </>
            ) : (
              <Link href="/dashboard" className="flex items-center gap-2 px-4 py-2 bg-white/5 border border-white/10 rounded-full cursor-pointer hover:bg-white/10 transition-all">
                <UserCircle size={16} className="text-indigo-400" />
                <span className="text-xs font-bold text-slate-300">Dashboard</span>
              </Link>
            )}
          </div>
        </nav>
      </header>

      {/* ==========================================
          SECTION 1: HERO VIEW (Aliniat spre dreapta)
          ========================================== */}
      <section className="w-full h-screen snap-start shrink-0 flex items-center justify-center relative z-10 px-6 md:px-12 pt-24 overflow-hidden">
        <div className="max-w-[1440px] w-full flex flex-col lg:flex-row items-center justify-center gap-12 xl:gap-24">
          
          {/* Left Text Block - Centrat optim */}
          <section className="w-full lg:max-w-xl xl:max-w-2xl space-y-8 animate-in fade-in slide-in-from-left-4 duration-1000 lg:pl-6">
            <div className="space-y-4">
               <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-[10px] font-bold text-indigo-400 uppercase tracking-widest">
                <Sparkles size={10} /> Powered by AI Agents
              </div>
              <h1 className="text-6xl md:text-[90px] font-bold tracking-tighter leading-[0.95] bg-gradient-to-b from-white to-white/30 bg-clip-text text-transparent uppercase">
                Your career,<br />redefined.
              </h1>
            </div>
            <p className="text-lg md:text-xl text-slate-400 font-light max-w-lg leading-relaxed border-l border-white/10 pl-6">
              CV Analysis, smart recommendations, and learning paths. Everything optimized by AI for your success in tech.
            </p>
            <div className="flex gap-4 pt-4">
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

          {/* Right Chat Console Panel */}
          <div className="w-full max-w-[520px] h-[480px] animate-in fade-in slide-in-from-right-6 duration-1000 shrink-0">
            <div className="h-full bg-[#0b0f1a]/60 border border-white/10 backdrop-blur-3xl rounded-[40px] overflow-hidden flex flex-col shadow-2xl border-t border-l border-white/20">
              <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between bg-white/[0.01]">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 shadow-inner">
                    <Sparkles size={14} />
                  </div>
                  <span className="text-xs font-black tracking-widest uppercase text-slate-200">AI Assistant</span>
                </div>
                <div className="flex items-center gap-1.5">
                   <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]" />
                   <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Live</span>
                </div>
              </div>
              <div className="flex-1 overflow-hidden min-h-0">
                <ChatPanel />
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* ==========================================
          SECTION 2: WHAT MAKES US DIFFERENT (Why Us)
          ========================================== */}
      <section id="features" className="w-full h-screen snap-start shrink-0 flex items-center justify-center relative z-10 px-6 md:px-12 overflow-hidden bg-[#050a15]/40 border-y border-white/5">
        <div className="max-w-[1440px] w-full grid grid-cols-1 lg:grid-cols-12 gap-16 items-center">
          
          <div className="lg:col-span-5 space-y-4">
            <div className="flex items-center gap-2 text-indigo-400">
               <Layers size={14} />
               <span className="text-[10px] font-black uppercase tracking-[0.3em]">Architectural Delta</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-black uppercase tracking-tight text-white leading-tight">
              What makes us<br />radically different?
            </h2>
            <p className="text-sm font-medium text-slate-400 leading-relaxed max-w-sm">
              We eliminated surface-level automation. Our system operates via specialized, deterministic AI agents interacting through closed loops.
            </p>
          </div>

          <div className="lg:col-span-7 grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div className="bg-[#0b0f1a]/60 border border-white/5 p-6 rounded-[28px] shadow-xl backdrop-blur-md group hover:border-indigo-500/30 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center text-indigo-400 border border-indigo-500/20 mb-4 shadow-inner">
                <Cpu size={18} />
              </div>
              <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-2">Multi-Agent Sandbox</h3>
              <p className="text-xs font-medium text-slate-400 leading-relaxed">Separate LLM instances handle specialized pipelines. Your code compiler doesn't share context with behavioral matrices, preventing cross-leak data pollution.</p>
            </div>

            <div className="bg-[#0b0f1a]/60 border border-white/5 p-6 rounded-[28px] shadow-xl backdrop-blur-md group hover:border-emerald-500/30 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-400 border border-emerald-500/20 mb-4 shadow-inner">
                <Terminal size={18} />
              </div>
              <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-2">Isolated Sandbox Testing</h3>
              <p className="text-xs font-medium text-slate-400 leading-relaxed">Technical solutions run inside an ephemeral, safe secure terminal stack execution framework. We map actual execution speed against heavy memory test buffers.</p>
            </div>

            <div className="bg-[#0b0f1a]/60 border border-white/5 p-6 rounded-[28px] shadow-xl backdrop-blur-md group hover:border-amber-500/30 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 border border-amber-500/20 mb-4 shadow-inner">
                <Shield size={18} />
              </div>
              <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-2">Automated Cooldowns</h3>
              <p className="text-[11px] font-medium text-slate-400 leading-relaxed">Anti-bruteforce verification protocols prevent trial-by-luck test progression. Failure triggers an automated state freeze, prioritizing true technical review loops.</p>
            </div>

            <div className="bg-[#0b0f1a]/60 border border-white/5 p-6 rounded-[28px] shadow-xl backdrop-blur-md group hover:border-purple-500/30 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400 border border-purple-500/20 mb-4 shadow-inner">
                <Zap size={18} className="fill-current" />
              </div>
              <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-2">Real-Time Core Metrics</h3>
              <p className="text-xs font-medium text-slate-400 leading-relaxed">Every soft-skill chat dynamic message and code compilation impacts a centralized, encrypted readiness telemetry dataset.</p>
            </div>
          </div>

        </div>
      </section>

      {/* ==========================================
          SECTION 3: THE PROCESS
          ========================================== */}
      <section id="process" className="w-full h-screen snap-start shrink-0 flex items-center justify-center relative z-10 px-6 md:px-12 overflow-hidden">
        <div className="max-w-[1440px] w-full space-y-16">
          
          <div className="text-center space-y-2">
            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.4em]">Operational Sequence</p>
            <h2 className="text-4xl md:text-5xl font-black text-white uppercase tracking-tight">The Core Engineering Process</h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <div className="bg-[#0b0f1a]/60 border border-white/5 rounded-[28px] p-6 flex flex-col justify-between h-64 relative shadow-xl backdrop-blur-xl">
               <span className="text-4xl font-black text-white/5 absolute top-4 right-6 select-none font-mono">01</span>
               <div>
                 <p className="text-[9px] font-black text-indigo-400 uppercase tracking-widest mb-1">Phase Alpha</p>
                 <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-3">CV Vectoring</h3>
               </div>
               <p className="text-xs font-medium text-slate-400 leading-relaxed">File structure ingestion converts unformatted career artifacts into highly structured analytical vectors for processing.</p>
            </div>

            <div className="bg-[#0b0f1a]/60 border border-white/5 rounded-[28px] p-6 flex flex-col justify-between h-64 relative shadow-xl backdrop-blur-xl">
               <span className="text-4xl font-black text-white/5 absolute top-4 right-6 select-none font-mono">02</span>
               <div>
                 <p className="text-[9px] font-black text-indigo-400 uppercase tracking-widest mb-1">Phase Beta</p>
                 <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-3">Telemetry Base</h3>
               </div>
               <p className="text-xs font-medium text-slate-400 leading-relaxed">The parser engine defines your initial technical index rating, creating an automated baseline path model configuration.</p>
            </div>

            <div className="bg-[#0b0f1a]/60 border border-white/5 rounded-[28px] p-6 flex flex-col justify-between h-64 relative shadow-xl backdrop-blur-xl">
               <span className="text-4xl font-black text-white/5 absolute top-4 right-6 select-none font-mono">03</span>
               <div>
                 <p className="text-[9px] font-black text-indigo-400 uppercase tracking-widest mb-1">Phase Gamma</p>
                 <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-3">Curriculum Loop</h3>
               </div>
               <p className="text-xs font-medium text-slate-400 leading-relaxed">Complete custom modular training stacks. Interactive quizzes unlock path progression vectors dynamically over time.</p>
            </div>

            <div className="bg-[#0b0f1a]/60 border border-white/5 rounded-[28px] p-6 flex flex-col justify-between h-64 relative shadow-xl backdrop-blur-xl">
               <span className="text-4xl font-black text-white/5 absolute top-4 right-6 select-none font-mono">04</span>
               <div>
                 <p className="text-[9px] font-black text-indigo-400 uppercase tracking-widest mb-1">Phase Delta</p>
                 <h3 className="text-lg font-bold text-white uppercase tracking-tight mb-3">Live Simulation</h3>
               </div>
               <p className="text-xs font-medium text-slate-400 leading-relaxed">Engage with specialized technical sandboxes and behavioral agents to match against high-intent corporate specifications.</p>
            </div>
          </div>

        </div>
      </section>

      {/* ==========================================
          SECTION 4: PRICING MATRIX & INTEGRATED FOOTER (Snap Slide Final)
          ========================================== */}
      <section id="pricing" className="w-full h-screen snap-start shrink-0 flex flex-col justify-between relative z-10 px-6 md:px-12 pt-28 pb-4 overflow-hidden bg-[#050a15]/40 border-t border-white/5">
        
        {/* Container flexibil central pentru Prețuri ca să nu existe nicio suprapunere */}
        <div className="max-w-[1440px] w-full mx-auto flex-1 flex flex-col justify-center space-y-10">
          <div className="text-center space-y-2 shrink-0">
            <p className="text-[10px] font-black text-indigo-400 uppercase tracking-[0.4em]">Commercial Parameters</p>
            <h2 className="text-4xl md:text-5xl font-black text-white uppercase tracking-tight leading-none">Subscription Structures</h2>
          </div>

          {/* Pricing Grid Layout */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-6xl mx-auto items-stretch relative w-full shrink-0">
            {PRICING_PLANS.map((plan, idx) => (
              <div 
                key={idx}
                className={cn(
                  "rounded-[24px] p-6 xl:p-8 border flex flex-col justify-between transition-all duration-500 relative bg-[#0b0f1a]",
                  plan.premium 
                    ? "border-indigo-500/40 shadow-[0_0_40px_rgba(99,102,241,0.12)] z-10" 
                    : "border-white/5 opacity-90"
                )}
              >
                {plan.premium && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-indigo-600 text-[8px] font-black uppercase tracking-widest text-white shadow-md z-20">
                     Recommended Vector
                  </div>
                )}

                <div className="space-y-4">
                  <div>
                    <h3 className="text-base font-black uppercase tracking-wide text-white">{plan.name}</h3>
                    <p className="text-xs text-slate-500 mt-1 leading-relaxed">{plan.desc}</p>
                  </div>

                  <div className="flex items-baseline gap-1 border-b border-white/5 pb-3">
                    <span className="text-3xl font-black text-white">${plan.price}</span>
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">/ {plan.period}</span>
                  </div>

                  <ul className="space-y-2">
                    {plan.features.map((feat, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs font-medium text-slate-300 leading-tight">
                        <CheckCircle2 size={13} className={cn("shrink-0 mt-0.5", plan.premium ? "text-indigo-400" : "text-slate-600")} />
                        {feat}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-6">
                  <button 
                    className={cn(
                      "w-full py-3 rounded-xl font-black text-[10px] uppercase tracking-widest transition-all active:scale-[0.98] outline-none border",
                      plan.premium 
                        ? "bg-white text-black border-transparent hover:bg-indigo-500 hover:text-white shadow-xl shadow-indigo-600/10" 
                        : "bg-white/5 text-slate-300 border-white/5 hover:bg-white/10"
                    )}
                  >
                    {plan.cta}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* --- COMPACT LOWER FOOTER - Integrat curat la baza ultimei secțiuni --- */}
        <footer className="w-full border-t border-white/5 flex items-center justify-between px-6 h-12 bg-transparent max-w-[1440px] mx-auto shrink-0 mt-4">
          <p className="text-[10px] font-black text-slate-600 tracking-[0.2em] uppercase leading-none">
            © 2026 CAREERPATH INTELLIGENCE • ALL RUNTIMES RESERVED
          </p>
          <div className="flex gap-6 text-[10px] font-black text-slate-600 uppercase tracking-widest leading-none">
             <span className="hover:text-slate-400 transition-colors cursor-pointer">System Operational</span>
             <span className="hover:text-slate-400 transition-colors cursor-pointer">GDPR Compliant</span>
          </div>
        </footer>

      </section>

    </div>
  );
}