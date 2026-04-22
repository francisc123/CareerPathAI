"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { loginSchema } from "@/lib/validations/auth";
import { api } from "@/lib/api-client";
import { useAuthStore } from "@/store/auth.store";
import { mockAuthResponse } from "@/lib/mocks/auth";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const [isLoading, setIsLoading] = React.useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" }
  });

  async function onSubmit(data: LoginFormValues) {
    setIsLoading(true);
    try {
      console.log("Apelare API cu:", data);
      
      // Simulare apel API real folosind Axios
      // În viitor: const res = await api.post("/auth/login", data);
      await new Promise(r => setTimeout(r, 1500));
      const res = { data: mockAuthResponse }; // Simulăm răspunsul de la backend

      // Salvăm în Zustand (care persistă automat în localStorage datorită configurării din CP-011)
      setAuth(res.data.user, res.data.token);
      
      router.push("/dashboard");
    } catch (error) {
      console.error("Eroare la autentificare:", error);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <Card className="border-gray-800 bg-gray-900/50 backdrop-blur-sm text-white shadow-2xl">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">Autentificare</CardTitle>
        <CardDescription className="text-gray-400 text-center">Intră în contul tău CareerPath AI</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" {...register("email")} className="bg-gray-800 border-gray-700" />
            {errors.email && <p className="text-xs text-red-500 font-medium">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Parolă</Label>
            <Input id="password" type="password" {...register("password")} className="bg-gray-800 border-gray-700" />
            {errors.password && <p className="text-xs text-red-500 font-medium">{errors.password.message}</p>}
          </div>
          <Button type="submit" className="w-full mt-4" disabled={isLoading}>
            {isLoading ? "Se verifică datele..." : "Conectare"}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="flex justify-center border-t border-gray-800 pt-4 text-sm text-gray-400">
        Nu ai cont? <Link href="/register" className="ml-1 text-primary hover:underline">Creează unul aici</Link>
      </CardFooter>
    </Card>
  );
}