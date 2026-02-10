"use client";

import { useEffect, useRef } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./message-bubble";
import { ChatInput } from "./chat-input";
import { useChat } from "@/hooks/use-chat";
import type { Message } from "@/types";

interface ChatContainerProps {
  conversationId: string;
  initialMessages?: Message[];
}

export function ChatContainer({
  conversationId,
  initialMessages = [],
}: ChatContainerProps) {
  const {
    messages,
    isStreaming,
    streamedContent,
    sendMessage,
    stopStreaming,
    setMessages,
  } = useChat(conversationId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (initialMessages.length > 0) {
      setMessages(initialMessages);
    }
  }, [initialMessages, setMessages]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, streamedContent]);

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <ScrollArea className="flex-1 px-4" ref={scrollRef}>
        <div className="mx-auto max-w-3xl space-y-4 py-4">
          {messages.length === 0 && !isStreaming && (
            <div className="py-20 text-center">
              <h2 className="text-2xl font-bold text-white">
                Social<span className="text-purple-400">Genius</span> IA
              </h2>
              <p className="mt-2 text-slate-400">
                Envía un mensaje para empezar. Puedo ayudarte con:
              </p>
              <div className="mx-auto mt-6 grid max-w-md gap-2">
                {[
                  "Analizar mi negocio y audiencia",
                  "Crear una estrategia de contenido",
                  "Generar un calendario editorial semanal",
                  "Escribir captions optimizados",
                  "Investigar hashtags y tendencias",
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => sendMessage(suggestion)}
                    className="rounded-lg border border-slate-700 p-3 text-left text-sm text-slate-300 transition-colors hover:border-purple-500/50 hover:bg-slate-800"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isStreaming && streamedContent && (
            <MessageBubble
              message={{
                id: "streaming",
                conversation_id: conversationId,
                role: "assistant",
                content: streamedContent,
                token_count: null,
                model_used: null,
                metadata_json: null,
                created_at: new Date().toISOString(),
              }}
              isStreaming
            />
          )}
        </div>
      </ScrollArea>
      <div className="border-t border-slate-800 px-4 py-4">
        <div className="mx-auto max-w-3xl">
          <ChatInput
            onSend={sendMessage}
            isStreaming={isStreaming}
            onStop={stopStreaming}
          />
        </div>
      </div>
    </div>
  );
}
