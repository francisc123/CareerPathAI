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
  { icon: FileUp, label: "Upload CV", href: "/upload" },
  { icon: Briefcase, label: "Jobs", href: "/jobs" },
  { icon: GraduationCap, label: "Learning", href: "/learning" },
  { icon: Users, label: "Interviews HR", href: "/interviews-hr" },
  { icon: Code, label: "Interviews Tech", href: "/interviews-tech" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="w-64 h-full bg-white/[0.01] border-r border-white/5 flex flex-col p-6 relative z-20 backdrop-blur-xl">
      
      {/* Navigație curată, centrată pe elementele de meniu */}
      <nav className="flex-1 space-y-2 pt-4">
        {menuItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center gap-4 px-4 py-3 rounded-2xl transition-all duration-300 border border-transparent",
                isActive 
                  ? "bg-indigo-500/10 text-white border-indigo-500/20 shadow-[0_0_20px_rgba(99,102,241,0.05)]" 
                  : "text-slate-500 hover:text-slate-200 hover:bg-white/5"
              )}
            >
              <item.icon 
                size={18} 
                className={cn(
                  "transition-colors duration-300",
                  isActive ? "text-indigo-400" : "group-hover:text-white"
                )} 
              />
              <span className={cn(
                "text-xs font-bold tracking-wide uppercase transition-all",
                isActive ? "opacity-100" : "opacity-70 group-hover:opacity-100"
              )}>
                {item.label}
              </span>
              
              {/* Indicator activ tip punct luminos */}
              {isActive && (
                <div className="ml-auto w-1 h-1 rounded-full bg-indigo-500 shadow-[0_0_8px_#6366f1]" />
              )}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}