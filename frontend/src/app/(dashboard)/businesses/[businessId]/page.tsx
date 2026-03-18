"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api-client";
import type { Business } from "@/types";

export default function BusinessDetailPage() {
  const params = useParams();
  const router = useRouter();
  const businessId = params.businessId as string;

  const [business, setBusiness] = useState<Business | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    industry: "",
    description: "",
    target_audience: "",
    brand_voice: "",
    website_url: "",
    instagram_handle: "",
    tiktok_handle: "",
  });

  useEffect(() => {
    api
      .get<Business>(`/businesses/${businessId}`)
      .then((data) => {
        setBusiness(data);
        setFormData({
          name: data.name,
          industry: data.industry,
          description: data.description,
          target_audience: data.target_audience || "",
          brand_voice: data.brand_voice || "",
          website_url: data.website_url || "",
          instagram_handle: data.instagram_handle || "",
          tiktok_handle: data.tiktok_handle || "",
        });
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [businessId]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await api.patch<Business>(`/businesses/${businessId}`, formData);
      setBusiness(updated);
      setIsEditing(false);
    } catch (error) {
      console.error("Error al guardar:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("¿Estás seguro de que quieres eliminar este negocio? Esta acción no se puede deshacer.")) {
      return;
    }
    setIsDeleting(true);
    try {
      await api.delete(`/businesses/${businessId}`);
      router.push("/businesses");
    } catch (error) {
      console.error("Error al eliminar:", error);
      setIsDeleting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64 bg-slate-800" />
        <Skeleton className="h-96 bg-slate-800" />
      </div>
    );
  }

  if (!business) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Negocio no encontrado</p>
        <Link href="/businesses">
          <Button variant="link" className="text-purple-400 mt-2">
            Volver a negocios
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl font-bold text-white sm:text-2xl">{business.name}</h1>
          <Badge variant="outline" className="mt-1 border-slate-700 text-slate-400">
            {business.industry}
          </Badge>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href={`/chat`}>
            <Button variant="outline" className="border-slate-600 text-white hover:bg-slate-800 text-sm">
              Chatear
            </Button>
          </Link>
          {isEditing ? (
            <>
              <Button
                variant="outline"
                className="border-slate-600 text-white hover:bg-slate-800 text-sm"
                onClick={() => setIsEditing(false)}
              >
                Cancelar
              </Button>
              <Button
                className="bg-purple-600 hover:bg-purple-700 text-sm"
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? "Guardando..." : "Guardar"}
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="outline"
                className="border-slate-600 text-white hover:bg-slate-800 text-sm"
                onClick={() => setIsEditing(true)}
              >
                Editar
              </Button>
              <Button
                variant="destructive"
                className="text-sm"
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? "Eliminando..." : "Eliminar"}
              </Button>
            </>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white">Información General</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-slate-400">Nombre</label>
              {isEditing ? (
                <Input
                  className="mt-1 border-slate-700 bg-slate-800 text-white"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                />
              ) : (
                <p className="mt-1 text-white">{business.name}</p>
              )}
            </div>
            <div>
              <label className="text-sm text-slate-400">Industria</label>
              {isEditing ? (
                <Input
                  className="mt-1 border-slate-700 bg-slate-800 text-white"
                  value={formData.industry}
                  onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                />
              ) : (
                <p className="mt-1 text-white">{business.industry}</p>
              )}
            </div>
            <div>
              <label className="text-sm text-slate-400">Descripción</label>
              {isEditing ? (
                <textarea
                  className="mt-1 w-full rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white"
                  rows={3}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              ) : (
                <p className="mt-1 text-white">{business.description}</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white">Audiencia y Marca</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-slate-400">Audiencia Objetivo</label>
              {isEditing ? (
                <Input
                  className="mt-1 border-slate-700 bg-slate-800 text-white"
                  value={formData.target_audience}
                  onChange={(e) => setFormData({ ...formData, target_audience: e.target.value })}
                />
              ) : (
                <p className="mt-1 text-white">
                  {business.target_audience || "No especificada"}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm text-slate-400">Voz de Marca</label>
              {isEditing ? (
                <Input
                  className="mt-1 border-slate-700 bg-slate-800 text-white"
                  value={formData.brand_voice}
                  onChange={(e) => setFormData({ ...formData, brand_voice: e.target.value })}
                />
              ) : (
                <p className="mt-1 text-white">
                  {business.brand_voice || "No especificada"}
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-white">Redes Sociales</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="text-sm text-slate-400">Sitio Web</label>
              {isEditing ? (
                <Input
                  className="mt-1 border-slate-700 bg-slate-800 text-white"
                  value={formData.website_url}
                  onChange={(e) => setFormData({ ...formData, website_url: e.target.value })}
                  placeholder="https://..."
                />
              ) : (
                <p className="mt-1 text-white">
                  {business.website_url || "No especificado"}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm text-slate-400">Instagram</label>
              {isEditing ? (
                <Input
                  className="mt-1 border-slate-700 bg-slate-800 text-white"
                  value={formData.instagram_handle}
                  onChange={(e) => setFormData({ ...formData, instagram_handle: e.target.value })}
                  placeholder="@usuario"
                />
              ) : (
                <p className="mt-1 text-white">
                  {business.instagram_handle ? `@${business.instagram_handle}` : "No configurado"}
                </p>
              )}
            </div>
            <div>
              <label className="text-sm text-slate-400">TikTok</label>
              {isEditing ? (
                <Input
                  className="mt-1 border-slate-700 bg-slate-800 text-white"
                  value={formData.tiktok_handle}
                  onChange={(e) => setFormData({ ...formData, tiktok_handle: e.target.value })}
                  placeholder="@usuario"
                />
              ) : (
                <p className="mt-1 text-white">
                  {business.tiktok_handle ? `@${business.tiktok_handle}` : "No configurado"}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
