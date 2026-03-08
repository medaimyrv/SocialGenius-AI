"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import { CONVERSATION_TYPE_LABELS } from "@/lib/constants";
import type { Business, Conversation, ConversationType } from "@/types";

const conversationTypes: {
  type: ConversationType;
  description: string;
}[] = [
  {
    type: "business_analysis",
    description: "Analiza tu negocio, audiencia y competidores",
  },
  {
    type: "content_strategy",
    description: "Genera una estrategia completa de contenido",
  },
  {
    type: "calendar_creation",
    description: "Crea un calendario editorial semanal",
  },
  {
    type: "copywriting",
    description: "Escribe captions, hooks y CTAs optimizados",
  },
  {
    type: "hashtag_research",
    description: "Investiga hashtags y tendencias relevantes",
  },
  {
    type: "general",
    description: "Pregunta lo que quieras sobre marketing digital",
  },
];

export default function ChatPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string>("");
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<Business[]>("/businesses"),
      api.get<Conversation[]>("/conversations"),
    ]).then(([biz, convs]) => {
      setBusinesses(biz);
      setConversations(convs);
      if (biz.length > 0) setSelectedBusiness(biz[0].id);
    });
  }, []);

  const startConversation = async (type: ConversationType) => {
    setIsCreating(true);
    try {
      const conversation = await api.post<Conversation>("/conversations", {
        business_id: selectedBusiness || null,
        conversation_type: type,
        title: CONVERSATION_TYPE_LABELS[type],
      });
      router.push(`/chat/${conversation.id}`);
    } catch (error) {
      console.error(error);
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Chat con IA</h1>
        <p className="text-slate-400">
          Selecciona un tipo de conversación para comenzar
        </p>
      </div>

      {/* Business selector */}
      {businesses.length > 0 && (
        <div className="space-y-2">
          <label className="text-sm text-slate-300">Negocio</label>
          <select
            value={selectedBusiness}
            onChange={(e) => setSelectedBusiness(e.target.value)}
            className="w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white"
          >
            <option value="">Sin negocio vinculado</option>
            {businesses.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} - {b.industry}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Conversation types */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {conversationTypes.map(({ type, description }) => (
          <Card
            key={type}
            className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50"
            onClick={() => !isCreating && startConversation(type)}
          >
            <CardHeader>
              <CardTitle className="text-sm text-purple-400">
                {CONVERSATION_TYPE_LABELS[type]}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">{description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent conversations */}
      {conversations.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-white">
            Conversaciones recientes
          </h2>
          <div className="space-y-2">
            {conversations.slice(0, 10).map((conv) => (
              <Card
                key={conv.id}
                className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-slate-700"
                onClick={() => router.push(`/chat/${conv.id}`)}
              >
                <CardContent className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm text-white">{conv.title}</p>
                    <p className="text-xs text-slate-500">
                      {new Date(conv.updated_at).toLocaleDateString("es-ES")}
                    </p>
                  </div>
                  <Badge
                    variant="outline"
                    className="border-slate-700 text-slate-400"
                  >
                    {CONVERSATION_TYPE_LABELS[conv.conversation_type]}
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
