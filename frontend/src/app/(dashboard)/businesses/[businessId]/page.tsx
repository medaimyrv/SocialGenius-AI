"use client";

import { useEffect, useRef, useState } from "react";
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

interface Document {
  id: string;
  filename: string;
  content_type: string;
  chunk_count: number;
  created_at: string;
}

export default function BusinessDetailPage() {
  const params = useParams();
  const router = useRouter();
  const businessId = params.businessId as string;

  const [business, setBusiness] = useState<Business | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Documentos RAG
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
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

    api.get<Document[]>(`/documents/${businessId}`)
      .then(setDocuments)
      .catch(() => {});
  }, [businessId]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setUploadError("");
    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = localStorage.getItem("access_token");
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/documents/${businessId}`,
        { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData }
      );
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Error al subir");
      }
      const newDoc = await res.json();
      setDocuments((prev) => [...prev, { ...newDoc, created_at: new Date().toISOString() }]);
    } catch (err: unknown) {
      setUploadError(err instanceof Error ? err.message : "Error al subir");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm("¿Eliminar este documento del RAG?")) return;
    try {
      await api.delete(`/documents/${businessId}/${docId}`);
      setDocuments((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      console.error(err);
    }
  };

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

        {/* Documentos RAG */}
        <Card className="border-slate-800 bg-slate-900 md:col-span-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white">Documentos RAG</CardTitle>
                <p className="mt-1 text-xs text-slate-500">
                  Sube PDFs o TXTs — el asistente los usará como contexto en el chat
                </p>
              </div>
              <div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,.md"
                  className="hidden"
                  onChange={handleUpload}
                />
                <Button
                  size="sm"
                  className="bg-purple-600 hover:bg-purple-700 text-xs"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                >
                  {isUploading ? "Subiendo..." : "+ Subir documento"}
                </Button>
              </div>
            </div>
            {uploadError && (
              <p className="mt-2 text-xs text-red-400">{uploadError}</p>
            )}
          </CardHeader>
          <CardContent>
            {documents.length === 0 ? (
              <p className="text-sm text-slate-500">
                No hay documentos. Sube una guía de marca, lista de productos o FAQ.
              </p>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center justify-between rounded-md border border-slate-800 bg-slate-950 px-3 py-2"
                  >
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="text-lg">
                        {doc.content_type === "application/pdf" ? "📄" : "📝"}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm text-white">{doc.filename}</p>
                        <p className="text-xs text-slate-500">{doc.chunk_count} fragmentos indexados</p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="shrink-0 text-slate-500 hover:text-red-400"
                      onClick={() => handleDeleteDocument(doc.id)}
                    >
                      ✕
                    </Button>
                  </div>
                ))}
              </div>
            )}
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
