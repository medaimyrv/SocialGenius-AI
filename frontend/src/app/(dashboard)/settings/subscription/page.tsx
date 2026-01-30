"use client";

import { useEffect, useState } from "react";
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
import type { Subscription } from "@/types";

function UsageMeter({
  label,
  used,
  max,
}: {
  label: string;
  used: number;
  max: number | null;
}) {
  const percentage = max ? Math.min((used / max) * 100, 100) : 0;
  const isUnlimited = max === null;

  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300">
          {used}
          {isUnlimited ? " (ilimitado)" : ` / ${max}`}
        </span>
      </div>
      {!isUnlimited && (
        <div className="h-2 rounded-full bg-slate-800">
          <div
            className={`h-full rounded-full transition-all ${
              percentage >= 90
                ? "bg-red-500"
                : percentage >= 70
                  ? "bg-yellow-500"
                  : "bg-purple-500"
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  );
}

export default function SubscriptionPage() {
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api
      .get<Subscription>("/subscriptions/status")
      .then(setSubscription)
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <Skeleton className="h-96 bg-slate-800" />;
  }

  if (!subscription) return null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Suscripcion</h1>
        <p className="text-slate-400">Tu plan actual y uso</p>
      </div>

      <Card className="border-slate-800 bg-slate-900">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white">
                Plan{" "}
                <Badge
                  className={
                    subscription.plan_tier === "pro"
                      ? "bg-purple-600"
                      : "bg-slate-700"
                  }
                >
                  {subscription.plan_tier.toUpperCase()}
                </Badge>
              </CardTitle>
              <CardDescription className="mt-1 text-slate-400">
                Estado: {subscription.status}
              </CardDescription>
            </div>
            {subscription.plan_tier === "free" && (
              <Button className="bg-purple-600 hover:bg-purple-700">
                Upgrade a Pro
              </Button>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <UsageMeter
            label="Estrategias"
            used={subscription.strategies_used_this_month}
            max={subscription.max_strategies}
          />
          <UsageMeter
            label="Calendarios"
            used={subscription.calendars_used_this_month}
            max={subscription.max_calendars}
          />
          <UsageMeter
            label="Mensajes"
            used={subscription.messages_used_this_month}
            max={subscription.max_messages}
          />
        </CardContent>
      </Card>
    </div>
  );
}
