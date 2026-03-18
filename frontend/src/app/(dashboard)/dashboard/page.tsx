"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import type { Business } from "@/types";

const STEPS = [
  {
    number: 1,
    title: "Crea tu perfil de negocio",
    desc: "Cuéntanos sobre tu negocio, industria y audiencia. La IA usará esta información para personalizar todo el contenido.",
    cta: "Crear negocio",
    href: "/businesses/new",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
  },
  {
    number: 2,
    title: "Chatea con la IA",
    desc: "Pide estrategias de contenido, calendarios editoriales, copywriting para Instagram y TikTok, o análisis de tu negocio.",
    cta: "Ir al chat",
    href: "/chat",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
      </svg>
    ),
  },
  {
    number: 3,
    title: "Revisa y publica",
    desc: "Edita el contenido generado, ajusta los detalles y tenlo listo para publicar en tus redes sociales.",
    cta: "Ver contenido",
    href: "/content",
    icon: (
      <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get<Business[]>("/businesses")
      .then(setBusinesses)
      .finally(() => setIsLoading(false));
  }, []);

  const hasBusinesses = businesses.length > 0;

  // Determinar el paso activo
  const activeStep = hasBusinesses ? 2 : 1;

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-purple-400 border-t-transparent" />
      </div>
    );
  }

  // Onboarding wizard (sin negocios)
  if (!hasBusinesses) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-8">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-purple-600/20">
            <svg className="h-8 w-8 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white sm:text-3xl">
            Bienvenido, {user?.full_name?.split(" ")[0] || ""}
          </h1>
          <p className="mt-2 text-slate-400">
            Sigue estos 3 pasos para empezar a generar contenido con IA
          </p>
        </div>

        {/* Steps wizard */}
        <div className="space-y-3">
          {STEPS.map((step, idx) => {
            const isDone = step.number < activeStep;
            const isActive = step.number === activeStep;
            const isLocked = step.number > activeStep;

            return (
              <div
                key={step.number}
                className={`relative rounded-xl border p-4 sm:p-5 transition-all ${
                  isActive
                    ? "border-purple-500 bg-purple-600/10 shadow-lg shadow-purple-900/20"
                    : isDone
                    ? "border-green-500/40 bg-green-900/10"
                    : "border-slate-800 bg-slate-900 opacity-50"
                }`}
              >
                <div className="flex items-start gap-4">
                  {/* Icono / número */}
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold ${
                      isDone
                        ? "bg-green-600 text-white"
                        : isActive
                        ? "bg-purple-600 text-white"
                        : "bg-slate-700 text-slate-400"
                    }`}
                  >
                    {isDone ? (
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                      </svg>
                    ) : (
                      step.number
                    )}
                  </div>

                  {/* Contenido */}
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                      <div>
                        <p className={`font-semibold ${isActive ? "text-white" : isDone ? "text-green-400" : "text-slate-500"}`}>
                          {step.title}
                        </p>
                        <p className={`mt-0.5 text-sm ${isActive ? "text-slate-300" : "text-slate-500"}`}>
                          {step.desc}
                        </p>
                      </div>
                      {isActive && (
                        <Link href={step.href} className="shrink-0">
                          <Button className="mt-3 w-full bg-purple-600 hover:bg-purple-700 sm:mt-0 sm:w-auto">
                            {step.cta} →
                          </Button>
                        </Link>
                      )}
                      {isDone && (
                        <span className="shrink-0 text-sm font-medium text-green-400">Completado</span>
                      )}
                      {isLocked && (
                        <span className="shrink-0 text-sm text-slate-600">Bloqueado</span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Línea conectora */}
                {idx < STEPS.length - 1 && (
                  <div className={`absolute left-[1.85rem] top-full h-3 w-0.5 ${isDone ? "bg-green-600/40" : "bg-slate-700"}`} />
                )}
              </div>
            );
          })}
        </div>

        <p className="mt-6 text-center text-xs text-slate-600">
          Solo toma 2 minutos · Puedes editar todo después
        </p>
      </div>
    );
  }

  // Dashboard normal (con negocios)
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white sm:text-3xl">
          Hola, {user?.full_name?.split(" ")[0] || ""}
        </h1>
        <p className="mt-1 text-slate-400">
          Tu asistente de estrategia de contenido con IA
        </p>
      </div>

      {/* Acciones rápidas */}
      <div className="grid gap-3 grid-cols-2 sm:gap-4 lg:grid-cols-4">
        <Link href="/chat">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Chat IA</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-slate-400 sm:text-sm">Inicia una conversación</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/businesses/new">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Nuevo Negocio</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-slate-400 sm:text-sm">Agrega un perfil</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/calendar">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Calendarios</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-slate-400 sm:text-sm">Calendarios editoriales</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/content">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Contenido</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-slate-400 sm:text-sm">Biblioteca generada</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Primeros pasos interactivos */}
      <Card className="border-slate-800 bg-slate-900">
        <CardHeader>
          <CardTitle className="text-white">Primeros pasos</CardTitle>
          <CardDescription className="text-slate-400">
            Sigue estos pasos para sacar el máximo provecho
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          {STEPS.map((step, idx) => {
            const isDone = step.number === 1 && hasBusinesses;
            const isActive = !isDone;

            return (
              <div
                key={step.number}
                className={`flex items-start gap-4 rounded-lg p-3 transition-colors ${
                  isDone ? "opacity-60" : "hover:bg-slate-800/50"
                }`}
              >
                <div
                  className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white ${
                    isDone ? "bg-green-600" : idx === 1 ? "bg-purple-600" : "bg-slate-700"
                  }`}
                >
                  {isDone ? (
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-medium text-white">{step.title}</p>
                    <p className="text-sm text-slate-400">{step.desc}</p>
                  </div>
                  {!isDone && (
                    <Link href={step.href} className="shrink-0">
                      <Button
                        size="sm"
                        className={idx === 1 ? "bg-purple-600 hover:bg-purple-700" : "border-slate-700 text-white hover:bg-slate-800"}
                        variant={idx === 1 ? "default" : "outline"}
                      >
                        {step.cta}
                      </Button>
                    </Link>
                  )}
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
