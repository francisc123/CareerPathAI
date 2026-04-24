import { Sidebar } from "@/components/sidebar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-black">
      <Sidebar />
      <div className="pl-64">
        {/* TopBar simplu inclus direct în layout */}
        <header className="h-16 border-b border-gray-800 flex items-center justify-end px-8 bg-black/50 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="text-right mr-2">
              <p className="text-xs font-bold text-white uppercase tracking-widest">Vlad Savu</p>
              <p className="text-[10px] text-primary font-bold">PRO ACCOUNT</p>
            </div>
            <div className="h-9 w-9 rounded-full bg-gray-800 border border-gray-700 flex items-center justify-center text-sm font-bold text-white">
              VS
            </div>
          </div>
        </header>
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
}