"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { loginSchema } from "@/lib/validations/auth"; // Verifică acest import!
import { useAuthStore } from "@/store/auth.store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { AlertCircle } from "lucide-react";

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [isLoading, setIsLoading] = React.useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const { 
    register, 
    handleSubmit, 
    formState: { errors, dirtyFields } 
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    mode: "onChange",
    defaultValues: { email: "", password: "" }
  });

  const [errorMsg, setErrorMsg] = React.useState<string | null>(null);

  async function onSubmit(data: LoginFormValues) {
    setIsLoading(true);
    setErrorMsg(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
      const res = await fetch(`${apiUrl}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: data.email, password: data.password }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        setErrorMsg(body?.message || "Login failed");
        return;
      }
      setAuth(body.user, body.token);
      router.push("/dashboard");
    } catch (e: any) {
      setErrorMsg(e?.message || "Network error");
    } finally {
      setIsLoading(false);
    }
  }

  const shouldShowError = (fieldName: string) => {
    return !!errors[fieldName as keyof typeof errors] && !!dirtyFields[fieldName as keyof typeof dirtyFields];
  };

  const inputErrorClass = (fieldName: string) => 
    shouldShowError(fieldName) 
      ? 'border-red-500/60 bg-red-500/5 focus:border-red-500 ring-1 ring-red-500/20' 
      : 'focus:border-indigo-500/50';

  return (
    <Card className="w-full max-w-[420px] border-white/5 bg-white/[0.01] backdrop-blur-3xl text-white shadow-2xl rounded-[32px] overflow-hidden">
      <CardContent className="pt-10 pb-8 px-10 text-center">
        {/* Abstract Nexus Logo */}
        <div className="flex justify-center mb-6">
          <div className="relative w-11 h-11">
             <div className="absolute inset-0 bg-indigo-500 rounded-full animate-pulse opacity-20" />
             <div className="absolute inset-0 border-2 border-indigo-400 rounded-full" />
             <div className="absolute inset-0 border-2 border-white/30 rounded-full rotate-45 scale-75" />
             <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-white rounded-full shadow-[0_0_8px_#fff]" />
          </div>
        </div>
        
        <h1 className="text-2xl font-bold tracking-tight mb-1 text-white">Welcome Back</h1>
        <p className="text-slate-500 text-xs italic mb-8 font-medium">Sign in to your CareerPath AI account</p>

        {errorMsg && (
          <div className="mb-4 px-3 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-300 text-[11px] font-bold text-left flex items-center gap-2">
            <AlertCircle size={14} /> {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 text-left">
          <div className="space-y-1.5">
            <Label className={`text-[10px] font-black uppercase tracking-[0.2em] ml-1 transition-colors ${shouldShowError("email") ? 'text-red-400' : 'text-slate-500'}`}>
              Account Email
            </Label>
            <div className="relative">
              <Input 
                {...register("email")} 
                placeholder="name@domain.com" 
                className={`bg-white/5 border-white/10 rounded-xl h-11 text-xs text-white placeholder:text-slate-600 transition-all ${inputErrorClass("email")}`} 
              />
              {shouldShowError("email") && <AlertCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none" />}
            </div>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between items-center px-1">
              <Label className={`text-[10px] font-black uppercase tracking-[0.2em] transition-colors ${shouldShowError("password") ? 'text-red-400' : 'text-slate-500'}`}>
                Password
              </Label>
              <button type="button" className="text-[10px] text-indigo-400 font-bold uppercase hover:text-white transition-colors">Forgot?</button>
            </div>
            <div className="relative">
              <Input 
                type="password" 
                {...register("password")} 
                placeholder="••••••••" 
                className={`bg-white/5 border-white/10 rounded-xl h-11 text-xs text-white transition-all ${inputErrorClass("password")}`} 
              />
              {shouldShowError("password") && <AlertCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none" />}
            </div>
          </div>

          <Button 
            type="submit" 
            className="w-full h-11 bg-white text-black hover:bg-slate-200 rounded-xl font-bold text-xs mt-4 active:scale-95 transition-all shadow-xl shadow-white/5" 
            disabled={isLoading}
          >
            {isLoading ? "Signing in..." : "Sign In"}
          </Button>
        </form>

        <div className="mt-8">
          <p className="text-[11px] text-slate-500 font-medium tracking-wide">
            New here? <Link href="/register" className="text-indigo-400 uppercase tracking-widest font-black hover:text-white transition-colors underline underline-offset-4 ml-1">Join now</Link>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}