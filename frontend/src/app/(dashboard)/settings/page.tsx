"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAuth } from "@/hooks/use-auth";

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Configuración</h1>
        <p className="text-slate-400">Gestiona tu cuenta</p>
      </div>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader>
          <CardTitle className="text-white">Perfil</CardTitle>
          <CardDescription className="text-slate-400">
            Información de tu cuenta
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm text-slate-400">Email</label>
            <p className="text-white">{user?.email}</p>
          </div>
          <div>
            <label className="text-sm text-slate-400">Nombre</label>
            <p className="text-white">{user?.full_name || "No configurado"}</p>
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader>
          <CardTitle className="text-white">Suscripción</CardTitle>
          <CardDescription className="text-slate-400">
            Gestiona tu plan y facturación
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link href="/settings/subscription">
            <Button
              variant="outline"
              className="border-slate-700 text-slate-300"
            >
              Ver plan y uso
            </Button>
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
