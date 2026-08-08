"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { canAccess, ROLE_HOME } from "@/lib/permissions";
import { Loader2 } from "lucide-react";

export function RouteGuard({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (isLoading) return;
    if (!user) return; // AuthContext handles redirect to /login

    const role = user.role;

    if (!canAccess(role, pathname)) {
      const home = ROLE_HOME[role] || "/inventory";
      router.replace(home);
    }
  }, [isLoading, user, pathname, router]);

  // While auth is loading, show a full-screen spinner
  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // If user is logged in but accessing a forbidden route, show nothing while redirecting
  if (user && !canAccess(user.role, pathname)) {
    return null;
  }

  return <>{children}</>;
}
