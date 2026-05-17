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
  { icon: Users, label: "Interviews HR", href: "/hr" },
  { icon: Code, label: "Interviews Tech", href: "/technical" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className={cn(
      "relative h-full z-40", 
      "w-[72px] hover:w-64", // Latime redusa pentru compactitate
      "bg-transparent", // Eliminam orice culoare diferita
      "flex flex-col py-4 transition-all duration-500 ease-[cubic-bezier(0.2,1,0.3,1)] group/sidebar", 
      "overflow-hidden"
    )}>
      
      <nav className="flex flex-col w-full">
        {menuItems.map((item) => {
          const isActive = item.href === "/dashboard" 
            ? pathname === "/dashboard" 
            : pathname.startsWith(item.href);
          
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "group flex items-center h-[56px] w-full transition-all duration-300 relative",
                "hover:bg-white/[0.03]"
              )}
            >
              {/* CONTAINER ICON - Centrare Matematica */}
              <div className="w-[72px] min-w-[72px] flex items-center justify-center relative z-10">
                <div className={cn(
                  "p-2.5 rounded-xl transition-all duration-300",
                  isActive ? "bg-indigo-500/20 text-indigo-400 shadow-[0_0_15px_rgba(99,102,241,0.2)]" : "text-slate-500 group-hover:text-slate-200"
                )}>
                  <item.icon size={20} />
                </div>
              </div>

              {/* LABEL - Glisare lina */}
              <span className={cn(
                "text-[10px] font-black tracking-[0.2em] uppercase transition-all duration-500 whitespace-nowrap",
                "opacity-0 -translate-x-4 group-hover/sidebar:opacity-100 group-hover/sidebar:translate-x-0",
                isActive ? "text-white" : "text-slate-400"
              )}>
                {item.label}
              </span>
              
              {/* Indicator activ discret in dreapta (doar la hover) */}
              {isActive && (
                <div className="absolute left-0 w-[2px] h-6 bg-indigo-500 shadow-[0_0_10px_#6366f1]" />
              )}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}