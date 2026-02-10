"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/lib/api-client";
import type { Business } from "@/types";

export default function NewBusinessPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    name: "",
    industry: "",
    description: "",
    target_audience: "",
    brand_voice: "",
    website_url: "",
    instagram_handle: "",
    tiktok_handle: "",
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>,
  ) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const business = await api.post<Business>("/businesses", {
        ...form,
        target_audience: form.target_audience || null,
        brand_voice: form.brand_voice || null,
        website_url: form.website_url || null,
        instagram_handle: form.instagram_handle || null,
        tiktok_handle: form.tiktok_handle || null,
      });
      router.push(`/businesses/${business.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al crear negocio");
    } finally {
      setIsLoading(false);
    }
  };

  const inputClass =
    "border-white/10 bg-white/5 text-white placeholder:text-slate-500";

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Nuevo Negocio</h1>
        <p className="text-slate-400">
          Agrega la información de tu negocio para que la IA pueda generar
          estrategias personalizadas
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white">Información básica</CardTitle>
            <CardDescription className="text-slate-400">
              Estos datos se usan para personalizar las estrategias de contenido
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="rounded-md bg-red-500/10 p-3 text-sm text-red-400">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-sm text-slate-300">
                Nombre del negocio *
              </label>
              <Input
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="Mi Negocio"
                required
                className={inputClass}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Industria *</label>
              <Input
                name="industry"
                value={form.industry}
                onChange={handleChange}
                placeholder="ej: Gastronomía, Fitness, Tecnología, Moda..."
                required
                className={inputClass}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Descripción *</label>
              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                placeholder="Describe tu negocio, productos/servicios principales..."
                required
                rows={3}
                className={`w-full rounded-md border px-3 py-2 text-sm ${inputClass}`}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">
                Audiencia objetivo
              </label>
              <Input
                name="target_audience"
                value={form.target_audience}
                onChange={handleChange}
                placeholder="ej: Mujeres 25-40, emprendedores, estudiantes..."
                className={inputClass}
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Voz de marca</label>
              <select
                name="brand_voice"
                value={form.brand_voice}
                onChange={handleChange}
                className={`w-full rounded-md border px-3 py-2 text-sm ${inputClass}`}
              >
                <option value="">Seleccionar...</option>
                <option value="profesional">Profesional</option>
                <option value="casual">Casual</option>
                <option value="divertido">Divertido</option>
                <option value="inspirador">Inspirador</option>
                <option value="educativo">Educativo</option>
                <option value="lujoso">Lujoso</option>
              </select>
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm text-slate-300">
                  Instagram handle
                </label>
                <Input
                  name="instagram_handle"
                  value={form.instagram_handle}
                  onChange={handleChange}
                  placeholder="minegocio"
                  className={inputClass}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm text-slate-300">TikTok handle</label>
                <Input
                  name="tiktok_handle"
                  value={form.tiktok_handle}
                  onChange={handleChange}
                  placeholder="minegocio"
                  className={inputClass}
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-sm text-slate-300">Sitio web</label>
              <Input
                name="website_url"
                value={form.website_url}
                onChange={handleChange}
                placeholder="https://minegocio.com"
                type="url"
                className={inputClass}
              />
            </div>
          </CardContent>
        </Card>
        <div className="mt-6 flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
            className="border-slate-700 text-slate-300"
          >
            Cancelar
          </Button>
          <Button
            type="submit"
            className="bg-purple-600 hover:bg-purple-700"
            disabled={isLoading}
          >
            {isLoading ? "Creando..." : "Crear Negocio"}
          </Button>
        </div>
      </form>
    </div>
  );
}
