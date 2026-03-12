"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
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

export default function DashboardPage() {
  const { user } = useAuth();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get<Business[]>("/businesses")
      .then(setBusinesses)
      .finally(() => setIsLoading(false));
  }, []);

  // Onboarding: usuario sin negocios
  if (!isLoading && businesses.length === 0) {
    return (
      <div className="flex min-h-[80vh] flex-col items-center justify-center px-4 text-center">
        <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full bg-purple-600/20">
          <svg className="h-10 w-10 text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-white">
          Bienvenido, {user?.full_name?.split(" ")[0] || ""}
        </h1>
        <p className="mt-3 max-w-md text-slate-400">
          Para empezar, cuéntanos sobre tu negocio. La IA usará esa información
          para generar estrategias de contenido personalizadas.
        </p>

        <div className="mt-8 w-full max-w-sm space-y-3">
          <Link href="/businesses/new">
            <Button className="w-full bg-purple-600 py-6 text-base hover:bg-purple-700">
              Crear mi perfil de negocio
            </Button>
          </Link>
          <p className="text-xs text-slate-500">
            Solo toma 2 minutos · Lo puedes editar después
          </p>
        </div>

        {/* Steps */}
        <div className="mt-12 grid max-w-lg gap-4 text-left sm:grid-cols-3">
          {[
            { step: "1", title: "Tu negocio", desc: "Describe tu negocio, industria y audiencia" },
            { step: "2", title: "Chat con IA", desc: "Pide estrategias, calendarios y contenido" },
            { step: "3", title: "Publica", desc: "Edita y publica en tus redes sociales" },
          ].map(({ step, title, desc }) => (
            <div key={step} className="rounded-lg border border-slate-800 bg-slate-900 p-4">
              <div className="mb-2 flex h-7 w-7 items-center justify-center rounded-full bg-purple-600 text-sm font-bold text-white">
                {step}
              </div>
              <p className="font-medium text-white">{title}</p>
              <p className="mt-1 text-xs text-slate-400">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">
          Hola, {user?.full_name || "Bienvenido"}
        </h1>
        <p className="mt-2 text-slate-400">
          Tu asistente de estrategia de contenido con IA
        </p>
      </div>

      {/* Quick actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link href="/chat">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Chat IA</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">Inicia una conversación con la IA</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/businesses/new">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Nuevo Negocio</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">Agrega un perfil de negocio</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/calendar">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Calendarios</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">Ver tus calendarios editoriales</p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/content">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">Contenido</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">Biblioteca de contenido generado</p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Getting started */}
      <Card className="border-slate-800 bg-slate-900">
        <CardHeader>
          <CardTitle className="text-white">Primeros pasos</CardTitle>
          <CardDescription className="text-slate-400">
            Sigue estos pasos para generar estrategias de contenido
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            { title: "Crea tu perfil de negocio", desc: "Agrega información sobre tu negocio, industria y audiencia objetivo", done: businesses.length > 0 },
            { title: "Chatea con la IA", desc: "Solicita análisis, estrategias, calendarios o copywriting", done: false },
            { title: "Revisa y publica", desc: "Edita el contenido generado y publícalo en tus redes", done: false },
          ].map(({ title, desc, done }, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white ${done ? "bg-green-600" : i === 0 ? "bg-purple-600" : "bg-slate-700"}`}>
                {done ? "✓" : i + 1}
              </div>
              <div>
                <p className="font-medium text-white">{title}</p>
                <p className="text-sm text-slate-400">{desc}</p>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
