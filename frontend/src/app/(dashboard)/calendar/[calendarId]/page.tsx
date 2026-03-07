"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api-client";
import { CONTENT_FORMAT_LABELS, PLATFORM_LABELS } from "@/lib/constants";
import type { ContentCalendar, ContentPiece } from "@/types";

const DAYS = [
  { key: "Lunes",     short: "Lun" },
  { key: "Martes",    short: "Mar" },
  { key: "Miércoles", short: "Mié" },
  { key: "Jueves",    short: "Jue" },
  { key: "Viernes",   short: "Vie" },
  { key: "Sábado",    short: "Sáb" },
  { key: "Domingo",   short: "Dom" },
];

function platformStyle(platform: string) {
  return platform === "instagram"
    ? { dot: "bg-pink-500", badge: "bg-pink-500/10 text-pink-400" }
    : { dot: "bg-cyan-400", badge: "bg-cyan-500/10 text-cyan-400" };
}

function PieceCard({
  piece,
  onDelete,
}: {
  piece: ContentPiece;
  onDelete: (id: string) => void;
}) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const style = platformStyle(piece.platform);

  async function handleDelete() {
    if (!confirming) {
      setConfirming(true);
      setTimeout(() => setConfirming(false), 3000);
      return;
    }
    setDeleting(true);
    try {
      await api.delete(`/content/${piece.id}`);
      onDelete(piece.id);
    } catch {
      setDeleting(false);
      setConfirming(false);
    }
  }

  return (
    <div className="group relative rounded-lg border border-slate-800 bg-slate-900 p-3 transition-all hover:border-purple-500/60 hover:bg-slate-800/60">
      {/* Platform color bar */}
      <div className={`absolute left-0 top-0 h-full w-1 rounded-l-lg ${style.dot}`} />

      <div className="pl-2 space-y-2">
        {/* Time + badges + delete */}
        <div className="flex items-start justify-between gap-1">
          <div className="flex items-center gap-1.5 flex-wrap">
            <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 ${style.badge}`}>
              {PLATFORM_LABELS[piece.platform]}
            </Badge>
            <Badge variant="outline" className="text-[10px] px-1.5 py-0 border-slate-700 text-slate-500">
              {CONTENT_FORMAT_LABELS[piece.content_format]}
            </Badge>
          </div>
          <div className="flex items-center gap-1 shrink-0">
            {piece.scheduled_time && (
              <span className="text-[10px] text-slate-500">
                {String(piece.scheduled_time).slice(0, 5)}
              </span>
            )}
            <button
              onClick={handleDelete}
              disabled={deleting}
              title={confirming ? "Clic para confirmar" : "Eliminar publicación"}
              className={`opacity-0 group-hover:opacity-100 transition-opacity rounded p-0.5 ${
                confirming
                  ? "opacity-100 text-red-400 bg-red-500/10"
                  : "text-slate-600 hover:text-red-400 hover:bg-red-500/10"
              }`}
            >
              <Trash2 size={12} />
            </button>
          </div>
        </div>

        {confirming && (
          <p className="text-[10px] text-red-400">Clic en 🗑 de nuevo para confirmar</p>
        )}

        {/* Topic */}
        <p className="text-xs font-semibold text-white leading-tight line-clamp-2">
          {piece.topic}
        </p>

        {/* Caption preview */}
        {piece.caption && (
          <p className="text-[11px] text-slate-400 leading-snug line-clamp-2">
            {piece.caption}
          </p>
        )}

        {/* Hashtags */}
        {piece.hashtags && piece.hashtags.length > 0 && (
          <p className="text-[10px] text-purple-400/60 truncate">
            {piece.hashtags.slice(0, 4).join(" ")}
          </p>
        )}
      </div>
    </div>
  );
}

function DayColumn({
  day,
  short,
  pieces,
  dateLabel,
  onDeletePiece,
}: {
  day: string;
  short: string;
  pieces: ContentPiece[];
  dateLabel?: string;
  onDeletePiece: (id: string) => void;
}) {
  const isEmpty = pieces.length === 0;
  return (
    <div className="flex flex-col min-h-[200px]">
      <div className={`mb-3 rounded-lg px-3 py-2 text-center ${isEmpty ? "bg-slate-900/40" : "bg-slate-800"}`}>
        <p className="text-xs font-bold uppercase tracking-widest text-slate-400">{short}</p>
        <p className="text-sm font-semibold text-white">{day}</p>
        {dateLabel && <p className="text-[10px] text-slate-500 mt-0.5">{dateLabel}</p>}
        {!isEmpty && (
          <span className="mt-1 inline-block rounded-full bg-purple-500/20 px-2 py-0.5 text-[10px] text-purple-300">
            {pieces.length} post{pieces.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      <div className="flex flex-col gap-2 flex-1">
        {isEmpty ? (
          <div className="flex flex-1 items-center justify-center rounded-lg border border-dashed border-slate-800 p-4">
            <span className="text-[11px] text-slate-600">Sin contenido</span>
          </div>
        ) : (
          pieces.map((p) => (
            <PieceCard key={p.id} piece={p} onDelete={onDeletePiece} />
          ))
        )}
      </div>
    </div>
  );
}

export default function CalendarDetailPage() {
  const params = useParams();
  const router = useRouter();
  const calendarId = params.calendarId as string;

  const [calendar, setCalendar] = useState<ContentCalendar | null>(null);
  const [pieces, setPieces] = useState<ContentPiece[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingCalendar, setDeletingCalendar] = useState(false);
  const [confirmDeleteCalendar, setConfirmDeleteCalendar] = useState(false);

  useEffect(() => {
    Promise.all([
      api.get<ContentCalendar>(`/calendars/${calendarId}`),
      api.get<ContentPiece[]>(`/content?calendar_id=${calendarId}`),
    ])
      .then(([calData, piecesData]) => {
        setCalendar(calData);
        setPieces(piecesData);
      })
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, [calendarId]);

  function handleDeletePiece(pieceId: string) {
    setPieces((prev) => prev.filter((p) => p.id !== pieceId));
  }

  async function handleDeleteCalendar() {
    if (!confirmDeleteCalendar) {
      setConfirmDeleteCalendar(true);
      setTimeout(() => setConfirmDeleteCalendar(false), 4000);
      return;
    }
    setDeletingCalendar(true);
    try {
      await api.delete(`/calendars/${calendarId}`);
      router.push("/calendar");
    } catch {
      setDeletingCalendar(false);
      setConfirmDeleteCalendar(false);
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-64 bg-slate-800" />
        <div className="grid grid-cols-7 gap-2">
          {Array.from({ length: 7 }).map((_, i) => (
            <Skeleton key={i} className="h-64 bg-slate-800" />
          ))}
        </div>
      </div>
    );
  }

  if (!calendar) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Calendario no encontrado</p>
        <Link href="/calendar" className="text-purple-400 hover:underline text-sm mt-2 inline-block">
          ← Volver a calendarios
        </Link>
      </div>
    );
  }

  const piecesByDay = DAYS.reduce<Record<string, ContentPiece[]>>((acc, d) => {
    acc[d.key] = pieces.filter(
      (p) => p.day_of_week?.toLowerCase() === d.key.toLowerCase()
    );
    return acc;
  }, {});

  const weekStartDate = calendar.week_start_date
    ? new Date(calendar.week_start_date + "T00:00:00")
    : null;

  const dateLabels = DAYS.reduce<Record<string, string>>((acc, d, i) => {
    if (weekStartDate) {
      const d2 = new Date(weekStartDate);
      d2.setDate(d2.getDate() + i);
      acc[d.key] = d2.toLocaleDateString("es-ES", { day: "numeric", month: "short" });
    }
    return acc;
  }, {});

  return (
    <div className="space-y-5">
      {/* Header */}
      <div>
        <Link href="/calendar" className="text-sm text-purple-400 hover:underline">
          ← Volver a calendarios
        </Link>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-white">{calendar.title}</h1>
            <div className="mt-2 flex flex-wrap gap-2">
              <Badge variant="secondary" className="bg-slate-800 text-slate-300">
                {calendar.week_start_date} → {calendar.week_end_date}
              </Badge>
              <Badge
                variant="outline"
                className={
                  calendar.status === "draft"
                    ? "border-yellow-600/50 text-yellow-400"
                    : "border-green-600/50 text-green-400"
                }
              >
                {calendar.status === "draft" ? "Borrador" : calendar.status}
              </Badge>
              <Badge variant="secondary" className="bg-purple-500/10 text-purple-300">
                {pieces.length} publicaciones
              </Badge>
            </div>
          </div>

          {/* Delete calendar button */}
          <Button
            variant="outline"
            size="sm"
            disabled={deletingCalendar}
            onClick={handleDeleteCalendar}
            className={`gap-2 border-slate-700 ${
              confirmDeleteCalendar
                ? "border-red-500/60 bg-red-500/10 text-red-400 hover:bg-red-500/20"
                : "text-slate-400 hover:border-red-500/60 hover:text-red-400"
            }`}
          >
            <Trash2 size={14} />
            {confirmDeleteCalendar ? "¿Confirmar eliminación?" : "Eliminar calendario"}
          </Button>
        </div>
      </div>

      {/* Strategy summary */}
      {calendar.strategy_summary && (
        <div className="rounded-lg border border-slate-800 bg-slate-900 px-4 py-3">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1">
            Estrategia
          </p>
          <p className="text-sm text-slate-300">{calendar.strategy_summary}</p>
        </div>
      )}

      {/* Weekly almanac grid */}
      <div className="overflow-x-auto pb-2">
        <div className="grid min-w-[900px] grid-cols-7 gap-2">
          {DAYS.map((d) => (
            <DayColumn
              key={d.key}
              day={d.key}
              short={d.short}
              pieces={piecesByDay[d.key] ?? []}
              dateLabel={dateLabels[d.key]}
              onDeletePiece={handleDeletePiece}
            />
          ))}
        </div>
      </div>

      {pieces.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-700 py-12 text-center">
          <p className="text-slate-400">Este calendario no tiene contenido.</p>
          <p className="mt-1 text-sm text-slate-500">
            Genera un nuevo calendario desde el chat para ver las publicaciones aquí.
          </p>
        </div>
      )}
    </div>
  );
}
