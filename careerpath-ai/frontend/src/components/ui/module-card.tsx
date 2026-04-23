import { BookOpen, Lock, CheckCircle2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface Props {
  title: string;
  week: number;
  status: "locked" | "active" | "completed";
  resources: number;
}

export function ModuleCard({ title, week, status, resources }: Props) {
  const isLocked = status === "locked";
  
  return (
    <div className={cn(
      "p-5 rounded-xl border transition-all",
      isLocked ? "bg-gray-900/50 border-gray-800 opacity-60" : "bg-gray-900 border-gray-700 hover:border-primary/50"
    )}>
      <div className="flex justify-between items-start mb-4">
        <div className="bg-gray-800 px-3 py-1 rounded-md text-xs font-mono text-primary border border-primary/20">
          SĂPTĂMÂNA {week}
        </div>
        {status === "completed" && <CheckCircle2 className="text-green-500" size={20} />}
        {status === "locked" && <Lock className="text-gray-600" size={20} />}
      </div>
      
      <h3 className="text-white font-bold text-lg mb-2">{title}</h3>
      
      <div className="flex items-center gap-2 text-sm text-gray-400 mb-5">
        <BookOpen size={14} />
        <span>{resources} resurse disponibile</span>
      </div>

      <Button 
        disabled={isLocked} 
        variant={status === "completed" ? "outline" : "default"}
        className="w-full"
      >
        {status === "completed" ? "Revedeți" : isLocked ? "Blocat" : "Începe"}
      </Button>
    </div>
  );
}