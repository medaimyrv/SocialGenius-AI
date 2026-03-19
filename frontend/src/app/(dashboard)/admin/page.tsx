"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api-client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

interface AdminUser {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  total_conversations: number;
  total_messages: number;
  last_login_at: string | null;
}

interface AdminUserListResponse {
  items: AdminUser[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

interface ActivityItem {
  id: string;
  user_id: string;
  user_email: string | null;
  event_type: string;
  created_at: string;
}

interface ActivityListResponse {
  items: ActivityItem[];
  total: number;
  total_pages: number;
}

const EVENT_BADGE: Record<string, string> = {
  login: "bg-blue-500/20 text-blue-300",
  register: "bg-green-500/20 text-green-300",
  new_conversation: "bg-purple-500/20 text-purple-300",
  send_message: "bg-slate-500/20 text-slate-300",
  calendar_created: "bg-yellow-500/20 text-yellow-300",
  strategy_generated: "bg-pink-500/20 text-pink-300",
  business_created: "bg-orange-500/20 text-orange-300",
};

export default function AdminPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  const [tab, setTab] = useState<"users" | "activity">("users");
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [loadingActivity, setLoadingActivity] = useState(false);
  const [emailFilter, setEmailFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<"" | "true" | "false">("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Solo admins pueden entrar
  useEffect(() => {
    if (!isLoading && user && user.role !== "admin") {
      router.push("/dashboard");
    }
  }, [user, isLoading, router]);

  const fetchUsers = async () => {
    setLoadingUsers(true);
    try {
      const params = new URLSearchParams({ page: String(page), page_size: "20" });
      if (emailFilter) params.set("email", emailFilter);
      if (activeFilter !== "") params.set("is_active", activeFilter);
      const data = await api.get<AdminUserListResponse>(`/admin/users?${params}`);
      setUsers(data.items);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch {
      // no-op
    } finally {
      setLoadingUsers(false);
    }
  };

  const fetchActivity = async () => {
    setLoadingActivity(true);
    try {
      const data = await api.get<ActivityListResponse>("/admin/activity?page_size=50");
      setActivity(data.items);
    } catch {
      // no-op
    } finally {
      setLoadingActivity(false);
    }
  };

  useEffect(() => {
    if (user?.role === "admin") fetchUsers();
  }, [user, page]);

  useEffect(() => {
    if (tab === "activity" && user?.role === "admin") fetchActivity();
  }, [tab, user]);

  const handleDeactivate = async (userId: string, isActive: boolean) => {
    const action = isActive ? "deactivate" : "reactivate";
    const label = isActive ? "desactivar" : "reactivar";
    if (!confirm(`¿Seguro que quieres ${label} este usuario?`)) return;
    setActionLoading(userId + action);
    setActionError(null);
    try {
      await api.patch(`/admin/users/${userId}/${action}`, {});
      await fetchUsers();
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Error al realizar la acción");
    } finally {
      setActionLoading(null);
    }
  };

  const handleDelete = async (userId: string, email: string) => {
    if (
      !confirm(
        `⚠️ ELIMINAR PERMANENTEMENTE\n\nUsuario: ${email}\n\nEsta acción es IRREVERSIBLE. ¿Continuar?`
      )
    )
      return;
    setActionLoading(userId + "delete");
    setActionError(null);
    try {
      await api.delete(`/admin/users/${userId}`);
      setUsers((prev) => prev.filter((u) => u.id !== userId));
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Error al eliminar usuario");
    } finally {
      setActionLoading(null);
    }
  };

  if (isLoading || !user) return null;
  if (user.role !== "admin") return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Panel de Administración</h1>
        <p className="text-slate-400">Gestión de usuarios y actividad de la plataforma</p>
      </div>

      {/* Stats rápidas */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Card className="border-slate-800 bg-slate-900">
          <CardContent className="py-4">
            <p className="text-2xl font-bold text-white">{total}</p>
            <p className="text-sm text-slate-400">Usuarios totales</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900">
          <CardContent className="py-4">
            <p className="text-2xl font-bold text-green-400">
              {users.filter((u) => u.is_active).length}
            </p>
            <p className="text-sm text-slate-400">Activos (pág. actual)</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900">
          <CardContent className="py-4">
            <p className="text-2xl font-bold text-purple-400">
              {users.reduce((s, u) => s + u.total_conversations, 0)}
            </p>
            <p className="text-sm text-slate-400">Conversaciones</p>
          </CardContent>
        </Card>
        <Card className="border-slate-800 bg-slate-900">
          <CardContent className="py-4">
            <p className="text-2xl font-bold text-blue-400">
              {users.reduce((s, u) => s + u.total_messages, 0)}
            </p>
            <p className="text-sm text-slate-400">Mensajes</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-800 pb-0">
        <button
          onClick={() => setTab("users")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            tab === "users"
              ? "border-b-2 border-purple-500 text-white"
              : "text-slate-400 hover:text-white"
          }`}
        >
          Usuarios
        </button>
        <button
          onClick={() => setTab("activity")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            tab === "activity"
              ? "border-b-2 border-purple-500 text-white"
              : "text-slate-400 hover:text-white"
          }`}
        >
          Actividad
        </button>
      </div>

      {/* ── TAB USUARIOS ── */}
      {tab === "users" && (
        <div className="space-y-4">
          {/* Filtros */}
          <div className="flex flex-col gap-3 sm:flex-row">
            <Input
              placeholder="Buscar por email..."
              value={emailFilter}
              onChange={(e) => setEmailFilter(e.target.value)}
              className="border-slate-700 bg-slate-800 text-white placeholder:text-slate-500 sm:max-w-xs"
            />
            <select
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value as "" | "true" | "false")}
              className="rounded-md border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white"
            >
              <option value="">Todos</option>
              <option value="true">Cuenta habilitada</option>
              <option value="false">Cuenta deshabilitada</option>
            </select>
            <Button
              onClick={() => { setPage(1); fetchUsers(); }}
              className="bg-purple-600 hover:bg-purple-700 text-sm"
            >
              Buscar
            </Button>
          </div>

          {actionError && (
            <div className="rounded-md border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-400">
              {actionError}
            </div>
          )}

          {/* Tabla */}
          <Card className="border-slate-800 bg-slate-900">
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-left text-slate-400">
                      <th className="px-4 py-3">Usuario</th>
                      <th className="px-4 py-3 hidden sm:table-cell">Rol</th>
                      <th className="px-4 py-3 hidden md:table-cell">Cuenta</th>
                      <th className="px-4 py-3 hidden lg:table-cell">Conversaciones</th>
                      <th className="px-4 py-3 hidden lg:table-cell">Último login</th>
                      <th className="px-4 py-3">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loadingUsers
                      ? Array.from({ length: 5 }).map((_, i) => (
                          <tr key={i} className="border-b border-slate-800">
                            <td className="px-4 py-3" colSpan={6}>
                              <Skeleton className="h-4 w-full bg-slate-800" />
                            </td>
                          </tr>
                        ))
                      : users.map((u) => (
                          <tr
                            key={u.id}
                            className="border-b border-slate-800 hover:bg-slate-800/50"
                          >
                            <td className="px-4 py-3">
                              <p className="font-medium text-white">{u.full_name ?? "—"}</p>
                              <p className="text-xs text-slate-400">{u.email}</p>
                            </td>
                            <td className="px-4 py-3 hidden sm:table-cell">
                              <Badge
                                className={
                                  u.role === "admin"
                                    ? "bg-purple-500/20 text-purple-300"
                                    : "bg-slate-700 text-slate-300"
                                }
                              >
                                {u.role}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 hidden md:table-cell">
                              <Badge
                                className={
                                  u.is_active
                                    ? "bg-green-500/20 text-green-300"
                                    : "bg-red-500/20 text-red-300"
                                }
                              >
                                {u.is_active ? "Habilitada" : "Deshabilitada"}
                              </Badge>
                            </td>
                            <td className="px-4 py-3 hidden lg:table-cell text-slate-300">
                              {u.total_conversations} conv · {u.total_messages} msg
                            </td>
                            <td className="px-4 py-3 hidden lg:table-cell text-slate-400 text-xs">
                              {u.last_login_at
                                ? new Date(u.last_login_at).toLocaleDateString("es")
                                : "Nunca"}
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex flex-wrap gap-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-slate-700 text-slate-300 hover:bg-slate-700 text-xs px-2"
                                  disabled={actionLoading === u.id + "deactivate" || actionLoading === u.id + "reactivate"}
                                  onClick={() => handleDeactivate(u.id, u.is_active)}
                                >
                                  {u.is_active ? "Desactivar" : "Reactivar"}
                                </Button>
                                <Button
                                  size="sm"
                                  variant="destructive"
                                  className="text-xs px-2"
                                  disabled={actionLoading === u.id + "delete"}
                                  onClick={() => handleDelete(u.id, u.email)}
                                >
                                  Eliminar
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                  </tbody>
                </table>
              </div>

              {/* Paginación */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between border-t border-slate-800 px-4 py-3">
                  <span className="text-xs text-slate-400">
                    Página {page} de {totalPages} · {total} usuarios
                  </span>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-slate-700 text-slate-300 text-xs"
                      disabled={page <= 1}
                      onClick={() => setPage((p) => p - 1)}
                    >
                      Anterior
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-slate-700 text-slate-300 text-xs"
                      disabled={page >= totalPages}
                      onClick={() => setPage((p) => p + 1)}
                    >
                      Siguiente
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── TAB ACTIVIDAD ── */}
      {tab === "activity" && (
        <Card className="border-slate-800 bg-slate-900">
          <CardHeader>
            <CardTitle className="text-white text-base">Actividad reciente</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-left text-slate-400">
                    <th className="px-4 py-3">Evento</th>
                    <th className="px-4 py-3">Usuario</th>
                    <th className="px-4 py-3">Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {loadingActivity
                    ? Array.from({ length: 8 }).map((_, i) => (
                        <tr key={i} className="border-b border-slate-800">
                          <td className="px-4 py-3" colSpan={3}>
                            <Skeleton className="h-4 w-full bg-slate-800" />
                          </td>
                        </tr>
                      ))
                    : activity.map((a) => (
                        <tr
                          key={a.id}
                          className="border-b border-slate-800 hover:bg-slate-800/50"
                        >
                          <td className="px-4 py-3">
                            <span
                              className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                                EVENT_BADGE[a.event_type] ?? "bg-slate-700 text-slate-300"
                              }`}
                            >
                              {a.event_type}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-slate-300 text-xs">
                            {a.user_email ?? a.user_id}
                          </td>
                          <td className="px-4 py-3 text-slate-400 text-xs">
                            {new Date(a.created_at).toLocaleString("es")}
                          </td>
                        </tr>
                      ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
