"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, FileUp, Briefcase, GraduationCap, Users, Code, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/auth.store";

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
  const logout = useAuthStore((state) => state.logout);

  return (
    <div className="w-64 h-screen bg-gray-950 border-r border-gray-800 flex flex-col p-4 fixed left-0 top-0 z-20">
      <div className="flex items-center gap-2 px-2 mb-10">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center font-bold text-white">C</div>
        <span className="text-xl font-bold text-white tracking-tighter">CareerPath AI</span>
      </div>

      <nav className="flex-1 space-y-1">
        {menuItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
              pathname === item.href 
                ? "bg-primary/10 text-primary border border-primary/20" 
                : "text-gray-400 hover:bg-gray-900 hover:text-white"
            )}
          >
            <item.icon size={18} />
            <span className="text-sm font-medium">{item.label}</span>
          </Link>
        ))}
      </nav>

      <button 
        onClick={() => logout()}
        className="flex items-center gap-3 px-3 py-2 text-gray-500 hover:text-red-400 transition-colors mt-auto border-t border-gray-800 pt-4"
      >
        <LogOut size={18} />
        <span className="text-sm font-medium">Deconectare</span>
      </button>
    </div>
  );
}