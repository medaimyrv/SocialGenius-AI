"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api-client";
import type { Message } from "@/types";

export function useChat(conversationId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamedContent, setStreamedContent] = useState("");
  const controllerRef = useRef<AbortController | null>(null);

  const loadMessages = useCallback(async () => {
    try {
      const conversation = await api.get<{ messages: Message[] }>(
        `/conversations/${conversationId}`,
      );
      const data = conversation as { messages?: Message[] };
      if (data && Array.isArray(data.messages)) {
        setMessages(data.messages);
      }
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  }, [conversationId]);

  const sendMessage = useCallback(
    (content: string) => {
      if (isStreaming) return;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        conversation_id: conversationId,
        role: "user",
        content,
        token_count: null,
        model_used: null,
        metadata_json: null,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsStreaming(true);
      setStreamedContent("");

      const controller = api.streamChat(
        conversationId,
        content,
        (chunk) => {
          setStreamedContent((prev) => prev + chunk);
        },
        () => {
          setStreamedContent((prev) => {
            const assistantMessage: Message = {
              id: crypto.randomUUID(),
              conversation_id: conversationId,
              role: "assistant",
              content: prev,
              token_count: null,
              model_used: null,
              metadata_json: null,
              created_at: new Date().toISOString(),
            };
            setMessages((msgs) => [...msgs, assistantMessage]);
            return "";
          });
          setIsStreaming(false);
        },
        (error) => {
          console.error("Chat error:", error);
          setIsStreaming(false);
          setStreamedContent("");
        },
      );
      controllerRef.current = controller;
    },
    [conversationId, isStreaming],
  );

  const stopStreaming = useCallback(() => {
    controllerRef.current?.abort();
    setIsStreaming(false);
  }, []);

  return {
    messages,
    isStreaming,
    streamedContent,
    sendMessage,
    stopStreaming,
    loadMessages,
    setMessages,
  };
}
