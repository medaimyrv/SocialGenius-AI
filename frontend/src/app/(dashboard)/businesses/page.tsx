"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api-client";
import type { Business } from "@/types";

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .get<Business[]>("/businesses")
      .then(setBusinesses)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Negocios</h1>
          <p className="text-slate-400">Gestiona tus perfiles de negocio</p>
        </div>
        <Link href="/businesses/new">
          <Button className="bg-purple-600 hover:bg-purple-700">
            Nuevo Negocio
          </Button>
        </Link>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-48 bg-slate-800" />
          ))}
        </div>
      ) : businesses.length === 0 ? (
        <Card className="border-slate-800 bg-slate-900">
          <CardContent className="py-12 text-center">
            <p className="text-slate-400">
              No tienes negocios registrados aún
            </p>
            <Link href="/businesses/new">
              <Button className="mt-4 bg-purple-600 hover:bg-purple-700">
                Crear tu primer negocio
              </Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {businesses.map((business) => (
            <Link key={business.id} href={`/businesses/${business.id}`}>
              <Card className="cursor-pointer border-slate-800 bg-slate-900 transition-colors hover:border-purple-500/50">
                <CardHeader>
                  <CardTitle className="text-white">{business.name}</CardTitle>
                  <CardDescription>
                    <Badge variant="outline" className="border-slate-700 text-slate-400">
                      {business.industry}
                    </Badge>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="line-clamp-2 text-sm text-slate-400">
                    {business.description}
                  </p>
                  <div className="mt-3 flex gap-2">
                    {business.instagram_handle && (
                      <Badge variant="secondary" className="bg-slate-800 text-slate-300">
                        @{business.instagram_handle}
                      </Badge>
                    )}
                    {business.tiktok_handle && (
                      <Badge variant="secondary" className="bg-slate-800 text-slate-300">
                        @{business.tiktok_handle}
                      </Badge>
                    )}
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
