import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";

interface Props {
  role: "user" | "ai";
  content: string;
  isTyping?: boolean;
}

export function ChatBubble({ role, content, isTyping }: Props) {
  const isAI = role === "ai";
  
  return (
    <div className={cn("flex w-full gap-3 mb-4", isAI ? "justify-start" : "justify-end")}>
      {isAI && <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center text-primary border border-primary/20 shrink-0"><Bot size={18}/></div>}
      <div className={cn(
        "max-w-[80%] rounded-2xl px-4 py-2 text-sm",
        isAI ? "bg-gray-800 text-gray-200 rounded-tl-none" : "bg-primary text-white rounded-tr-none"
      )}>
        {isTyping ? (
          <div className="flex gap-1 py-1">
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" />
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
            <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]" />
          </div>
        ) : content}
      </div>
      {!isAI && <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center text-gray-300 border border-gray-600 shrink-0"><User size={18}/></div>}
    </div>
  );
}