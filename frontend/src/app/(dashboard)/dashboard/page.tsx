"use client";

import Link from "next/link";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";

export default function DashboardPage() {
  const { user } = useAuth();

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
              <CardTitle className="text-sm text-purple-400">
                Chat IA
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">
                Inicia una conversación con la IA
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/businesses/new">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">
                Nuevo Negocio
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">
                Agrega un perfil de negocio
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/calendar">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">
                Calendarios
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">
                Ver tus calendarios editoriales
              </p>
            </CardContent>
          </Card>
        </Link>
        <Link href="/content">
          <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm text-purple-400">
                Contenido
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-slate-400">
                Biblioteca de contenido generado
              </p>
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Getting started */}
      <Card className="border-slate-800 bg-slate-900">
        <CardHeader>
          <CardTitle className="text-white">Primeros pasos</CardTitle>
          <CardDescription className="text-slate-400">
            Sigue estos pasos para empezar a generar estrategias de contenido
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-purple-600 text-sm font-bold text-white">
              1
            </div>
            <div>
              <p className="font-medium text-white">Crea tu perfil de negocio</p>
              <p className="text-sm text-slate-400">
                Agrega información sobre tu negocio, industria y audiencia objetivo
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-sm font-bold text-white">
              2
            </div>
            <div>
              <p className="font-medium text-white">Chatea con la IA</p>
              <p className="text-sm text-slate-400">
                Solicita análisis, estrategias, calendarios o copywriting
              </p>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-slate-700 text-sm font-bold text-white">
              3
            </div>
            <div>
              <p className="font-medium text-white">Revisa y publica</p>
              <p className="text-sm text-slate-400">
                Edita el contenido generado y publícalo en tus redes
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
