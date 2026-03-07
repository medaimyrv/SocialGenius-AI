"use client";

import { cn } from "@/lib/utils";
import type { Message } from "@/types";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

export function MessageBubble({ message, isStreaming }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[80%] rounded-2xl px-4 py-3",
          isUser ? "bg-purple-600 text-white" : "bg-slate-800 text-slate-200",
        )}
      >
        <div className="whitespace-pre-wrap text-sm leading-relaxed">
          {message.content}
          {isStreaming && (
            <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-purple-400" />
          )}
        </div>

        {!isUser && message.model_used && (
          <p className="mt-2 text-xs text-slate-500">{message.model_used}</p>
        )}
      </div>
    </div>
  );
}
