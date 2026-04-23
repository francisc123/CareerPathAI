"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { registerSchema } from "@/lib/validations/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterPage() {
  const [isLoading, setIsLoading] = React.useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "", confirmPassword: "" }
  });

  async function onSubmit(data: RegisterFormValues) {
    setIsLoading(true);
    console.log("Register date:", data);
    await new Promise(r => setTimeout(r, 1500));
    setIsLoading(false);
    alert("Cont creat!");
  }

  return (
    <Card className="border-gray-800 bg-gray-900/50 backdrop-blur-sm text-white shadow-2xl">
      <CardHeader>
        <CardTitle className="text-2xl font-bold text-center">Înregistrare</CardTitle>
        <CardDescription className="text-gray-400 text-center">Creează un cont nou pentru a începe</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Nume complet</Label>
            <Input id="name" {...register("name")} className="bg-gray-800 border-gray-700" />
            {errors.name && <p className="text-xs text-red-500">{errors.name.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" {...register("email")} className="bg-gray-800 border-gray-700" />
            {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Parolă</Label>
            <Input id="password" type="password" {...register("password")} className="bg-gray-800 border-gray-700" />
            {errors.password && <p className="text-xs text-red-500">{errors.password.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirmă parola</Label>
            <Input id="confirmPassword" type="password" {...register("confirmPassword")} className="bg-gray-800 border-gray-700" />
            {errors.confirmPassword && <p className="text-xs text-red-500">{errors.confirmPassword.message}</p>}
          </div>
          <Button type="submit" className="w-full mt-4" disabled={isLoading}>
            {isLoading ? "Se creează contul..." : "Înregistrare"}
          </Button>
        </form>
      </CardContent>
      <CardFooter className="flex justify-center border-t border-gray-800 pt-4 text-sm text-gray-400">
        Ai deja cont? <Link href="/login" className="ml-1 text-primary hover:underline">Autentifică-te</Link>
      </CardFooter>
    </Card>
  );
}