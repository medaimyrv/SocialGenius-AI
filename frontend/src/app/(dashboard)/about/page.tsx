"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const features = [
  {
    icon: "🧠",
    title: "RAG — Memoria Inteligente",
    badge: "Implementado",
    badgeColor: "bg-green-500/20 text-green-400 border-green-500/30",
    description:
      "Retrieval-Augmented Generation con ChromaDB. El asistente recuerda conversaciones anteriores, aprende del historial de tu negocio y recupera información relevante en tiempo real para darte respuestas cada vez más precisas.",
    details: [
      "Memoria de conversación dentro de la sesión",
      "Memoria persistente entre sesiones por negocio",
      "Búsqueda semántica con sentence-transformers (all-MiniLM-L6-v2)",
      "Vector store con ChromaDB persistente",
    ],
  },
  {
    icon: "📄",
    title: "Base de Conocimiento con Documentos",
    badge: "Implementado",
    badgeColor: "bg-green-500/20 text-green-400 border-green-500/30",
    description:
      "Sube PDFs, TXTs o notas de tu negocio y el asistente los usa como referencia. Tus guías de marca, listas de productos, FAQs y cualquier documento se convierten en contexto activo.",
    details: [
      "Soporte para PDF, TXT y Markdown",
      "Extracción automática de texto con PyPDF",
      "Chunking inteligente con overlap para mejor recuperación",
      "Indexación semántica por negocio",
    ],
  },
  {
    icon: "🤖",
    title: "Modelo de IA — Qwen 2.5 72B",
    badge: "Activo",
    badgeColor: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    description:
      "Potenciado por Qwen 2.5 72B Instruct vía HuggingFace Inference API. Un modelo de última generación con 72 mil millones de parámetros, especializado en razonamiento, escritura creativa y análisis de negocio.",
    details: [
      "72B parámetros — calidad de respuesta superior",
      "Streaming en tiempo real via SSE",
      "5 tipos de prompt especializados (estrategia, calendario, copywriting, hashtags, análisis)",
      "Optimizado para español e inglés",
    ],
  },
  {
    icon: "📅",
    title: "Generación Automática de Calendarios",
    badge: "Activo",
    badgeColor: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    description:
      "El asistente genera calendarios editoriales completos que se guardan automáticamente en tu cuenta. Incluye días, horarios, formatos, captions, hashtags y CTAs listos para publicar.",
    details: [
      "Parsing inteligente de respuestas IA",
      "Soporte Instagram (Reels, Carrusel, Stories) y TikTok",
      "Horarios óptimos de publicación",
      "Guardado automático en la plataforma",
    ],
  },
  {
    icon: "🔐",
    title: "Autenticación Segura",
    badge: "Activo",
    badgeColor: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    description:
      "Sistema de autenticación robusto con JWT y bcrypt. Los tokens se refrescan automáticamente para mantener la sesión activa sin interrupciones.",
    details: [
      "Contraseñas hasheadas con bcrypt",
      "Access token + Refresh token (JWT)",
      "Auto-refresh silencioso en el cliente",
      "Roles de usuario (admin / user)",
    ],
  },
  {
    icon: "👑",
    title: "Panel de Administración",
    badge: "Activo",
    badgeColor: "bg-purple-500/20 text-purple-400 border-purple-500/30",
    description:
      "Panel exclusivo para administradores con gestión completa de usuarios: ver registros, actividad, activar/desactivar cuentas y eliminar usuarios.",
    details: [
      "Listado de todos los usuarios registrados",
      "Activar / desactivar cuentas (soft delete)",
      "Eliminación permanente de usuarios",
      "Protegido por rol admin",
    ],
  },
];

const stack = [
  { name: "FastAPI", category: "Backend" },
  { name: "SQLAlchemy Async", category: "Backend" },
  { name: "PostgreSQL", category: "Backend" },
  { name: "ChromaDB", category: "RAG" },
  { name: "sentence-transformers", category: "RAG" },
  { name: "PyPDF", category: "RAG" },
  { name: "Qwen 2.5 72B", category: "IA" },
  { name: "HuggingFace API", category: "IA" },
  { name: "Next.js 14", category: "Frontend" },
  { name: "TailwindCSS", category: "Frontend" },
  { name: "shadcn/ui", category: "Frontend" },
  { name: "JWT + bcrypt", category: "Seguridad" },
];

const categoryColors: Record<string, string> = {
  Backend: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  RAG: "bg-green-500/20 text-green-400 border-green-500/30",
  IA: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  Frontend: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  Seguridad: "bg-red-500/20 text-red-400 border-red-500/30",
};

export default function AboutPage() {
  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">
          Acerca de <span className="text-purple-400">SocialGenius AI</span>
        </h1>
        <p className="mt-2 text-slate-400">
          Plataforma de estrategia de contenido potenciada por Inteligencia Artificial con memoria contextual avanzada.
        </p>
      </div>

      {/* Funcionalidades */}
      <div className="grid gap-4 grid-cols-1 lg:grid-cols-2">
        {features.map((f) => (
          <Card key={f.title} className="border-slate-800 bg-slate-900">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-2">
                <CardTitle className="flex items-center gap-2 text-base text-white sm:text-lg">
                  <span>{f.icon}</span>
                  {f.title}
                </CardTitle>
                <Badge
                  variant="outline"
                  className={`shrink-0 text-xs ${f.badgeColor}`}
                >
                  {f.badge}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-slate-400">{f.description}</p>
              <ul className="space-y-1">
                {f.details.map((d) => (
                  <li key={d} className="flex items-start gap-2 text-xs text-slate-500">
                    <span className="mt-0.5 text-purple-400">✓</span>
                    {d}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Stack tecnológico */}
      <div>
        <h2 className="mb-4 text-lg font-semibold text-white">Stack tecnológico</h2>
        <div className="flex flex-wrap gap-2">
          {stack.map((s) => (
            <Badge
              key={s.name}
              variant="outline"
              className={`text-xs ${categoryColors[s.category]}`}
            >
              {s.name}
            </Badge>
          ))}
        </div>
      </div>

      {/* Versión */}
      <p className="text-xs text-slate-600">
        SocialGenius AI v1.0 · Construido con FastAPI + Next.js 14 · Modelo Qwen 2.5 72B via HuggingFace
      </p>
    </div>
  );
}
