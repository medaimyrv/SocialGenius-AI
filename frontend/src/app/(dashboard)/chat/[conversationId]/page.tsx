"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ChatContainer } from "@/components/chat/chat-container";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api-client";
import type { Conversation, Message } from "@/types";

export default function ChatConversationPage() {
  const params = useParams();
  const conversationId = params.conversationId as string;
  const [conversation, setConversation] = useState<
    (Conversation & { messages: Message[] }) | null
  >(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .get<Conversation & { messages: Message[] }>(
        `/conversations/${conversationId}`,
      )
      .then(setConversation)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [conversationId]);

  if (isLoading) {
    return (
      <div className="space-y-4 p-8">
        <Skeleton className="h-8 w-64 bg-slate-800" />
        <Skeleton className="h-96 bg-slate-800" />
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="py-20 text-center text-slate-400">
        Conversacion no encontrada
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <h1 className="text-lg font-semibold text-white">
          {conversation.title}
        </h1>
      </div>
      <ChatContainer
        conversationId={conversationId}
        initialMessages={conversation.messages || []}
      />
    </div>
  );
}
