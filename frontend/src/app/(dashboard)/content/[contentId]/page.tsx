"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
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
import { CONTENT_FORMAT_LABELS, PLATFORM_LABELS } from "@/lib/constants";
import type { ContentPiece } from "@/types";

export default function ContentDetailPage() {
  const params = useParams();
  const contentId = params.contentId as string;

  const [piece, setPiece] = useState<ContentPiece | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [formData, setFormData] = useState({
    topic: "",
    caption: "",
    hook: "",
    call_to_action: "",
    visual_description: "",
    notes: "",
  });

  useEffect(() => {
    api
      .get<ContentPiece>(`/content/${contentId}`)
      .then((data) => {
        setPiece(data);
        setFormData({
          topic: data.topic,
          caption: data.caption,
          hook: data.hook || "",
          call_to_action: data.call_to_action || "",
          visual_description: data.visual_description || "",
          notes: data.notes || "",
        });
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [contentId]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const updated = await api.patch<ContentPiece>(`/content/${contentId}`, formData);
      setPiece(updated);
      setIsEditing(false);
    } catch (error) {
      console.error("Error al guardar:", error);
    } finally {
      setIsSaving(false);
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

  if (!piece) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Contenido no encontrado</p>
        <Link href="/content">
          <Button variant="link" className="text-purple-400 mt-2">
            Volver a contenido
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <Link href="/content" className="text-sm text-purple-400 hover:underline">
            &larr; Volver a contenido
          </Link>
          <h1 className="mt-2 text-2xl font-bold text-white">{piece.topic}</h1>
          <div className="mt-2 flex gap-2">
            <Badge
              variant="secondary"
              className={
                piece.platform === "instagram"
                  ? "bg-pink-500/10 text-pink-400"
                  : "bg-cyan-500/10 text-cyan-400"
              }
            >
              {PLATFORM_LABELS[piece.platform]}
            </Badge>
            <Badge variant="outline" className="border-slate-700 text-slate-400">
              {CONTENT_FORMAT_LABELS[piece.content_format]}
            </Badge>
            <Badge variant="outline" className="border-slate-700 text-slate-400">
              {piece.day_of_week} - {piece.scheduled_date}
            </Badge>
            {piece.scheduled_time && (
              <Badge variant="outline" className="border-slate-700 text-slate-400">
                {piece.scheduled_time}
              </Badge>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {isEditing ? (
            <>
              <Button
                variant="outline"
                className="border-slate-700 text-slate-300 hover:bg-slate-800"
                onClick={() => setIsEditing(false)}
              >
                Cancelar
              </Button>
              <Button
                className="bg-purple-600 hover:bg-purple-700"
                onClick={handleSave}
                disabled={isSaving}
              >
                {isSaving ? "Guardando..." : "Guardar"}
              </Button>
            </>
          ) : (
            <Button
              variant="outline"
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
              onClick={() => setIsEditing(true)}
            >
              Editar
            </Button>
          )}
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-900 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-white">Caption</CardTitle>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <textarea
                className="border-slate-700 bg-slate-800 text-white"
                rows={6}
                value={formData.caption}
                onChange={(e) => setFormData({ ...formData, caption: e.target.value })}
              />
            ) : (
              <p className="whitespace-pre-wrap text-slate-300">{piece.caption}</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white">Hook</CardTitle>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Input
                className="border-slate-700 bg-slate-800 text-white"
                value={formData.hook}
                onChange={(e) => setFormData({ ...formData, hook: e.target.value })}
                placeholder="Frase gancho para captar atención"
              />
            ) : (
              <p className="text-slate-300">{piece.hook || "Sin hook definido"}</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white">Call to Action</CardTitle>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <Input
                className="border-slate-700 bg-slate-800 text-white"
                value={formData.call_to_action}
                onChange={(e) => setFormData({ ...formData, call_to_action: e.target.value })}
                placeholder="Llamada a la acción"
              />
            ) : (
              <p className="text-slate-300">{piece.call_to_action || "Sin CTA definido"}</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white">Descripción Visual</CardTitle>
          </CardHeader>
          <CardContent>
            {isEditing ? (
              <textarea
                className="border-slate-700 bg-slate-800 text-white"
                rows={3}
                value={formData.visual_description}
                onChange={(e) => setFormData({ ...formData, visual_description: e.target.value })}
                placeholder="Descripción de la imagen o video"
              />
            ) : (
              <p className="text-slate-300">
                {piece.visual_description || "Sin descripción visual"}
              </p>
            )}
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white">Hashtags</CardTitle>
          </CardHeader>
          <CardContent>
            {piece.hashtags && piece.hashtags.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {piece.hashtags.map((tag, i) => (
                  <Badge key={i} variant="secondary" className="bg-purple-500/10 text-purple-400">
                    {tag}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-slate-500">Sin hashtags</p>
            )}
          </CardContent>
        </Card>

        {(piece.notes || isEditing) && (
          <Card className="border-slate-800 bg-slate-900 md:col-span-2">
            <CardHeader>
              <CardTitle className="text-white">Notas</CardTitle>
            </CardHeader>
            <CardContent>
              {isEditing ? (
                <textarea
                  className="border-slate-700 bg-slate-800 text-white"
                  rows={3}
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="Notas adicionales"
                />
              ) : (
                <p className="text-slate-300">{piece.notes}</p>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
