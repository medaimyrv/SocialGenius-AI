"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api-client";
import { PLATFORM_LABELS } from "@/lib/constants";
import type { ContentCalendar } from "@/types";

export default function CalendarPage() {
  const [calendars, setCalendars] = useState<ContentCalendar[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .get<ContentCalendar[]>("/calendars")
      .then(setCalendars)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Calendarios</h1>
        <p className="text-slate-400">
          Tus calendarios editoriales generados por IA
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[1, 2].map((i) => (
            <Skeleton key={i} className="h-40 bg-slate-800" />
          ))}
        </div>
      ) : calendars.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900">
          <CardContent className="py-12 text-center">
            <p className="text-slate-400">No tienes calendarios aun</p>
            <p className="mt-2 text-sm text-slate-500">
              Inicia un chat de tipo &quot;Crear Calendario&quot; para generar uno
            </p>
            <Link href="/chat">
              <span className="mt-4 inline-block text-purple-400 hover:underline">
                Ir al Chat
              </span>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {calendars.map((calendar) => (
            <Link key={calendar.id} href={`/calendar/${calendar.id}`}>
              <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-white">
                      {calendar.title}
                    </CardTitle>
                    <Badge
                      variant="outline"
                      className="border-slate-700 text-slate-400"
                    >
                      {calendar.status}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex gap-2 text-sm text-slate-400">
                    <span>{calendar.week_start_date}</span>
                    <span>-</span>
                    <span>{calendar.week_end_date}</span>
                  </div>
                  <Badge variant="secondary" className="bg-slate-800 text-slate-300">
                    {PLATFORM_LABELS[calendar.platform] || calendar.platform}
                  </Badge>
                  {calendar.strategy_summary && (
                    <p className="line-clamp-2 text-sm text-slate-500">
                      {calendar.strategy_summary}
                    </p>
                  )}
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
