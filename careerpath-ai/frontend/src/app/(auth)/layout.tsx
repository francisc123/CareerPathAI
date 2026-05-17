"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation"; // Hook-ul necesar pentru a detecta pagina
import { Globe, Zap, ShieldCheck } from "lucide-react";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  // Verificăm dacă suntem pe pagina de login sau register
  const isLoginPage = pathname === "/login";

  return (
    <div className="h-screen w-screen flex flex-col bg-[#020617] text-white overflow-hidden relative font-sans">
      {/* Background Decor */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-500/10 blur-[100px]" />
        <div className="absolute bottom-[-5%] right-[-5%] w-[30%] h-[30%] rounded-full bg-blue-500/5 blur-[100px]" />
      </div>

      {/* --- HEADER --- */}
      <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-6 py-6">
        <nav className="w-full max-w-[1440px] flex items-center justify-between px-8 py-3 bg-white/[0.02] border border-white/10 backdrop-blur-xl rounded-full shadow-lg">
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

          {/* CORECTAT: Înlocuit butoanele defecte cu Link-uri cross-page inteligente către secțiunile Landing Page-ului */}
          <div className="hidden md:flex items-center gap-8">
            <Link href="/#features" className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors outline-none">
              Why Us
            </Link>
            <Link href="/#process" className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors outline-none">
              The Process
            </Link>
            <Link href="/#pricing" className="text-[10px] font-black uppercase tracking-widest text-slate-500 hover:text-white transition-colors outline-none">
              Pricing
            </Link>
          </div>




          <div>
             {/* Comutator dinamic pentru butonul din Header */}
             {isLoginPage ? (
               <Link 
                href="/register" 
                className="text-[11px] font-black uppercase tracking-widest bg-white text-black px-6 py-2 rounded-full hover:bg-slate-200 transition-all active:scale-95 shadow-xl shadow-white/5"
               >
                Sign Up
               </Link>
             ) : (
               <Link 
                href="/login" 
                className="text-[11px] font-black uppercase tracking-widest bg-white text-black px-6 py-2 rounded-full hover:bg-slate-200 transition-all active:scale-95 shadow-xl shadow-white/5"
               >
                Sign In
               </Link>
             )}
          </div>
        </nav>
      </header>

      {/* Main content centering */}
      <main className="flex-1 flex items-center justify-center relative z-10 px-4 pt-20">
        {children}
      </main>
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