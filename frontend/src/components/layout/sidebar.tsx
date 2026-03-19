"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { Separator } from "@/components/ui/separator";

const navItems = [
  { href: "/dashboard", label: "Inicio", icon: "M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
  { href: "/businesses", label: "Negocios", icon: "M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" },
  { href: "/chat", label: "Chat IA", icon: "M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" },
  { href: "/calendar", label: "Calendario", icon: "M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" },
  { href: "/content", label: "Contenido", icon: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" },
];

interface SidebarProps {
  onClose?: () => void;
}

export function Sidebar({ onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-800 bg-slate-950">
      {/* Logo */}
      <div className="flex h-14 items-center justify-between px-6 md:h-16">
        <Link href="/dashboard" className="text-xl font-bold text-white" onClick={onClose}>
          Social<span className="text-purple-400">Genius</span>
        </Link>
        {/* Close button — only visible on mobile */}
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-md p-1 text-slate-400 hover:text-white md:hidden"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      <Separator className="bg-slate-800" />

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <Link key={item.href} href={item.href} onClick={onClose}>
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-3 text-slate-400 hover:bg-slate-800 hover:text-white",
                pathname.startsWith(item.href) &&
                  "bg-purple-600/10 text-purple-400 hover:bg-purple-600/20 hover:text-purple-300",
              )}
            >
              <svg
                className="h-5 w-5 shrink-0"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
              </svg>
              {item.label}
            </Button>
          </Link>
        ))}

        {/* Acerca de */}
        <Link href="/about" onClick={onClose}>
          <Button
            variant="ghost"
            className={cn(
              "w-full justify-start gap-3 text-slate-400 hover:bg-slate-800 hover:text-white",
              pathname.startsWith("/about") &&
                "bg-purple-600/10 text-purple-400 hover:bg-purple-600/20 hover:text-purple-300",
            )}
          >
            <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Acerca de
          </Button>
        </Link>

        {/* Solo visible para admins */}
        {user?.role === "admin" && (
          <Link href="/admin" onClick={onClose}>
            <Button
              variant="ghost"
              className={cn(
                "w-full justify-start gap-3 text-slate-400 hover:bg-slate-800 hover:text-white",
                pathname.startsWith("/admin") &&
                  "bg-purple-600/10 text-purple-400 hover:bg-purple-600/20 hover:text-purple-300",
              )}
            >
              <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              Admin
            </Button>
          </Link>
        )}
      </nav>

      <Separator className="bg-slate-800" />

      {/* User section */}
      <div className="p-4">
        <Link href="/settings" onClick={onClose}>
          <Button
            variant="ghost"
            className="w-full justify-start gap-3 text-slate-400 hover:bg-slate-800 hover:text-white"
          >
            <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Configuración
          </Button>
        </Link>
        <div className="mt-2 flex items-center justify-between px-3">
          <span className="truncate text-sm text-slate-500">{user?.email}</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="text-slate-500 hover:text-red-400"
          >
            Salir
          </Button>
        </div>
      </div>
    </aside>
  );
}
