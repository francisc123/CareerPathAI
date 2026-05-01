import Link from "next/link";
import { UserCircle } from "lucide-react";

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 flex justify-center px-6 py-6 pointer-events-none">
      <nav className="w-full max-w-[1440px] flex items-center justify-between px-8 py-3 bg-white/[0.02] border border-white/10 backdrop-blur-xl rounded-full shadow-2xl pointer-events-auto">
        
        {/* LOGO NOU ABSTRACT */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative w-7 h-7">
            <div className="absolute inset-0 bg-indigo-500 rounded-full animate-pulse opacity-20" />
            <div className="absolute inset-0 border-2 border-indigo-400 rounded-full" />
            <div className="absolute inset-0 border-2 border-white/30 rounded-full rotate-45 scale-75" />
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#fff]" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="text-sm font-black tracking-[0.2em] uppercase text-white">CareerPath</span>
            <span className="text-[9px] text-indigo-400 font-bold tracking-[0.4em] uppercase opacity-80 leading-tight">Intelligence</span>
          </div>
        </Link>

        {/* NAVIGATIE DREAPTA - STIL PREMIUM */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3 pl-6 border-l border-white/10 group cursor-pointer">
            <div className="text-right hidden sm:block leading-none">
              <p className="text-[10px] font-black text-white uppercase tracking-widest mb-1">Vlad Savu</p>
              <p className="text-[9px] text-indigo-400 font-bold uppercase tracking-tighter">Pro Account</p>
            </div>
            <div className="h-9 w-9 rounded-full bg-white/5 border border-white/10 flex items-center justify-center group-hover:border-indigo-500/50 transition-all">
              <UserCircle size={20} className="text-slate-400 group-hover:text-white transition-colors" />
            </div>
          </div>
        </div>
      </nav>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="w-full py-8 text-center bg-transparent border-t border-white/5 mt-auto relative z-10">
      <div className="flex items-center justify-center gap-3 opacity-30">
        <div className="w-1 h-1 bg-indigo-500 rounded-full animate-pulse" />
        <span className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-300">
          &copy; {new Date().getFullYear()} CareerPath Intelligence
        </span>
      </div>
    </footer>
  );
}