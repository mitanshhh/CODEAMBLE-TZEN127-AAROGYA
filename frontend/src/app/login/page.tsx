"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import { ROLE_HOME } from "@/lib/permissions";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Hospital, User, Lock } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await login(username, password);
      // After login, user is set in context — get role from localStorage
      const role = localStorage.getItem("role") || "MEDICAL_OFFICER";
      const home = ROLE_HOME[role] || "/inventory";
      toast.success("Login successful!");
      router.push(home);
    } catch (err: any) {
      toast.error(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen w-full flex-1 bg-background flex flex-col py-8 px-4 sm:px-6 lg:px-8 relative overflow-x-hidden overflow-y-auto">
      {/* Background Image */}
      <div
        className="absolute inset-0 z-0 opacity-20"
        style={{
          backgroundImage: "url('https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?q=80&w=2753&auto=format&fit=crop')",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />
      <div className="absolute inset-0 z-0 bg-background/80 backdrop-blur-sm"></div>

      <div className="absolute inset-0 z-0">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-primary rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="m-auto w-full max-w-lg relative z-10 flex flex-col">
        <div className="flex justify-center">
          <div className="h-20 w-20 bg-background rounded-2xl flex items-center justify-center border border-primary/20 shadow-sm backdrop-blur-sm overflow-hidden p-2">
            <img src="/aarogya_logo.png" alt="Aarogya Logo" className="w-full h-full object-contain" />
          </div>
        </div>
        <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-foreground">
          Welcome to Aarogya
        </h2>
        <p className="mt-2 text-center text-sm text-muted-foreground">
          AI-Powered Health Centre Management System
        </p>

        <div className="mt-8 w-full">
          <div className="bg-card/60 backdrop-blur-xl py-8 px-4 shadow-[0_8px_30px_rgb(0,0,0,0.04)] sm:rounded-2xl sm:px-10 border border-border/50">
            <form className="space-y-6" onSubmit={handleLogin}>
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Username</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <User className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    id="username"
                    type="text"
                    required
                    autoComplete="username"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-border rounded-xl bg-background/50 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all duration-200"
                    placeholder="Enter your username"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-foreground mb-2">Password</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Lock className="h-5 w-5 text-muted-foreground" />
                  </div>
                  <input
                    id="password"
                    type="password"
                    required
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="block w-full pl-10 pr-3 py-2.5 border border-border rounded-xl bg-background/50 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all duration-200"
                    placeholder="Enter your password"
                  />
                </div>
              </div>

              <div>
                <Button
                  type="submit"
                  id="login-submit"
                  disabled={isLoading}
                  className="w-full flex justify-center py-2.5 px-4 rounded-xl text-sm font-medium shadow-md transition-all duration-200 hover:shadow-lg"
                >
                  {isLoading ? "Signing in..." : "Sign in"}
                </Button>
              </div>
            </form>

            <div className="mt-6 bg-background/60 p-4 rounded-xl border border-border/50 text-sm shadow-sm backdrop-blur-sm">
              <p className="font-semibold text-foreground/90 mb-3 text-center flex items-center justify-center gap-2">
                <Hospital className="w-4 h-4" /> Demo Accounts
              </p>
              <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-muted-foreground text-xs sm:text-sm">
                <div className="text-right font-medium">District Admin:</div>
                <div className="font-mono text-foreground">admin</div>

                <div className="text-right font-medium">Medical Officer:</div>
                <div className="font-mono text-foreground">mo_alpha</div>

                <div className="text-right font-medium">Receptionist:</div>
                <div className="font-mono text-foreground">recp_alpha</div>

                <div className="text-right font-medium">Doctor:</div>
                <div className="font-mono text-foreground">doctor_alpha</div>
              </div>
              <div className="mt-4 pt-3 border-t border-border/50 text-center text-xs text-muted-foreground">
                Password: <span className="font-mono text-foreground bg-background/80 px-2 py-1 rounded shadow-sm">password123</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
