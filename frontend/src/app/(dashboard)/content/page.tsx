"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api-client";
import { CONTENT_FORMAT_LABELS, PLATFORM_LABELS } from "@/lib/constants";
import type { ContentPiece } from "@/types";

export default function ContentPage() {
  const [pieces, setPieces] = useState<ContentPiece[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .get<ContentPiece[]>("/content")
      .then(setPieces)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Contenido</h1>
        <p className="text-slate-400">
          Todas las piezas de contenido generadas
        </p>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32 bg-slate-800" />
          ))}
        </div>
      ) : pieces.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900">
          <CardContent className="py-12 text-center">
            <p className="text-slate-400">No hay contenido generado aún</p>
            <p className="mt-2 text-sm text-slate-500">
              Genera un calendario editorial para crear piezas de contenido
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {pieces.map((piece) => (
            <Card
              key={piece.id}
              className="border-slate-800 bg-slate-900"
            >
              <CardContent className="py-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    <div className="flex gap-2">
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
                      <Badge
                        variant="outline"
                        className="border-slate-700 text-slate-400"
                      >
                        {CONTENT_FORMAT_LABELS[piece.content_format]}
                      </Badge>
                    </div>
                    <h3 className="font-medium text-white">{piece.topic}</h3>
                    <p className="line-clamp-2 text-sm text-slate-400">
                      {piece.caption}
                    </p>
                  </div>
                  <div className="text-right text-sm text-slate-500">
                    <p>{piece.day_of_week}</p>
                    <p>{piece.scheduled_date}</p>
                    {piece.scheduled_time && <p>{piece.scheduled_time}</p>}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
