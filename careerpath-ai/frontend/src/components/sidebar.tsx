"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  FileUp, 
  Briefcase, 
  GraduationCap, 
  Users, 
  Code 
} from "lucide-react";
import { cn } from "@/lib/utils";

const menuItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: GraduationCap, label: "Learning", href: "/learning/path" },
  { icon: FileUp, label: "Upload CV", href: "/upload" },
  { icon: Briefcase, label: "Jobs", href: "/jobs" },
  { icon: Users, label: "Interviews HR", href: "/interviews-hr" },
  { icon: Code, label: "Interviews Tech", href: "/interviews-tech" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 h-full bg-white/[0.01] border-r border-white/5 flex flex-col p-6 relative z-20 backdrop-blur-xl">
      
      <nav className="flex-1 space-y-2 pt-4">
        {menuItems.map((item) => {
          const isActive = item.href === "/dashboard" 
            ? pathname === "/dashboard" 
            : pathname.startsWith(item.href);
          
          return (
            <Link
              key={item.href}
              href={item.href}
              /* 
                 AM ADĂUGAT: 
                 1. transform-gpu -> Forțează randarea pe placa video (previne artefactele de blur)
                 2. backface-visibility-hidden -> Curăță pixelii "rămași" în urmă
              */
              className={cn(
                "group flex items-center gap-4 px-4 py-3 rounded-2xl transition-all duration-200 border border-transparent relative transform-gpu backface-visibility-hidden",
                isActive 
                  ? "bg-indigo-500/10 text-white border-indigo-500/20" 
                  : "text-slate-500 hover:text-slate-200 hover:bg-white/5"
              )}
            >
              <item.icon 
                size={18} 
                className={cn(
                  "transition-colors duration-200",
                  isActive ? "text-indigo-400" : "group-hover:text-white"
                )} 
              />
              <span className={cn(
                "text-xs font-bold tracking-wide uppercase transition-all",
                isActive ? "opacity-100" : "opacity-70 group-hover:opacity-100"
              )}>
                {item.label}
              </span>
              
              {isActive && (
                /* 
                   Am schimbat shadow-ul mare cu un ring-1 de indigo-500/50. 
                   Arată la fel dar nu generează artefacte de "lumină" care rămân pe ecran.
                */
                <div className="ml-auto w-1 h-1 rounded-full bg-indigo-500 ring-4 ring-indigo-500/20" />
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}