"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { registerSchema } from "@/lib/validations/auth";
import { useAuthStore } from "@/store/auth.store";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { ChevronDown, AlertCircle } from "lucide-react";

export default function RegisterPage() {
  const [step, setStep] = React.useState(1);
  const [isLoading, setIsLoading] = React.useState(false);
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);

  const { 
    register, 
    handleSubmit, 
    trigger, 
    formState: { errors, dirtyFields }, 
    clearErrors 
  } = useForm({
    resolver: zodResolver(registerSchema),
    mode: "onChange",
  });

  const nextStep = async () => {
    // Validăm strict doar câmpurile de pe pasul curent
    const currentFields = step === 1 ? ["name", "email"] : ["age", "education"];
    
    // @ts-ignore
    const isValid = await trigger(currentFields);
    
    if (isValid) {
      // Curățăm erorile pentru a preveni "scurgerea" lor pe pasul următor
      clearErrors();
      setStep(step + 1);
    }
  };

  async function onSubmit(data: any) {
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
      const response = await fetch(`${apiUrl}/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: data.name,
          email: data.email,
          age: data.age,
          education: data.education,
          password: data.password,
        }),
      });

      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        alert(`Înregistrare eșuată: ${result.message || "Eroare necunoscută"}`);
        return;
      }

      // Backend-ul ne trimite { user, token } — salvăm sesiunea și mergem mai departe
      if (result.user && result.token) {
        setAuth(result.user, result.token);
        router.push("/dashboard");
      } else {
        // fallback dacă backend-ul nu returnează token-ul (eveniment de regresie)
        router.push("/login");
      }
    } catch (error: any) {
      console.error("Eroare de rețea:", error);
      alert("Nu s-a putut conecta la server. Verifică dacă Gateway-ul rulează.");
    } finally {
      setIsLoading(false);
    }
  }

  /**
   * Logica CRITICĂ: Afișăm eroarea DOAR dacă:
   * 1. Câmpul a fost modificat (isDirty) - utilizatorul a scris ceva
   * 2. Există o eroare activă în obiectul errors
   */
  const shouldShowError = (fieldName: string) => {
    const hasError = !!errors[fieldName as keyof typeof errors];
    const isDirty = !!dirtyFields[fieldName as keyof typeof dirtyFields];
    
    // La pasul final, dacă dăm "Complete", dirty check-ul ar putea bloca erorile, 
    // așa că lăsăm trigger-ul de submit să decidă.
    return hasError && isDirty;
  };

  const inputErrorClass = (fieldName: string) => 
    shouldShowError(fieldName) 
      ? 'border-red-500/60 bg-red-500/5 focus:border-red-500 ring-1 ring-red-500/20' 
      : 'focus:border-indigo-500/50';

  return (
    <Card className="w-full max-w-[420px] border-white/5 bg-white/[0.01] backdrop-blur-3xl text-white shadow-2xl rounded-[32px] overflow-hidden transition-all duration-500">
      <style jsx global>{`
        /* Eliminăm săgețile de la input number */
        input::-webkit-outer-spin-button,
        input::-webkit-inner-spin-button {
          -webkit-appearance: none !important;
          margin: 0 !important;
        }
        input[type=number] {
          -moz-appearance: textfield !important;
        }
      `}</style>

      <CardContent className="pt-10 pb-8 px-10 text-center">
        {/* Nexus Logo */}
        <div className="flex justify-center mb-6">
          <div className="relative w-11 h-11">
             <div className="absolute inset-0 bg-indigo-500 rounded-full animate-pulse opacity-20" />
             <div className="absolute inset-0 border-2 border-indigo-400 rounded-full" />
             <div className="absolute inset-0 border-2 border-white/30 rounded-full rotate-45 scale-75" />
          </div>
        </div>

        <h1 className="text-2xl font-bold tracking-tight mb-1">Create Account</h1>
        <div className="flex items-center justify-center gap-1 mb-8">
            {[1, 2, 3].map((s) => (
                <div key={s} className={`h-1 rounded-full transition-all duration-300 ${step >= s ? "w-4 bg-indigo-500" : "w-2 bg-white/10"}`} />
            ))}
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 text-left min-h-[190px]">
          {/* STEP 1 */}
          {step === 1 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300 space-y-4">
              <div className="space-y-1.5">
                <Label className={`text-[10px] font-black uppercase tracking-[0.2em] ml-1 ${shouldShowError("name") ? 'text-red-400' : 'text-slate-500'}`}>Full Name</Label>
                <div className="relative">
                  <Input {...register("name")} placeholder="John Doe" className={`bg-white/5 border-white/10 rounded-xl h-11 text-xs text-white placeholder:text-slate-600 transition-all ${inputErrorClass("name")}`} />
                  {shouldShowError("name") && <AlertCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none" />}
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className={`text-[10px] font-black uppercase tracking-[0.2em] ml-1 ${shouldShowError("email") ? 'text-red-400' : 'text-slate-500'}`}>Email Address</Label>
                <div className="relative">
                  <Input {...register("email")} placeholder="john@example.com" className={`bg-white/5 border-white/10 rounded-xl h-11 text-xs text-white placeholder:text-slate-600 transition-all ${inputErrorClass("email")}`} />
                  {shouldShowError("email") && <AlertCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none" />}
                </div>
              </div>
            </div>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300 space-y-4">
              <div className="space-y-1.5">
                <Label className={`text-[10px] font-black uppercase tracking-[0.2em] ml-1 ${shouldShowError("age") ? 'text-red-400' : 'text-slate-500'}`}>Age (Min. 16)</Label>
                <div className="relative">
                  <Input type="number" {...register("age", { valueAsNumber: true })} placeholder="25" className={`bg-white/5 border-white/10 rounded-xl h-11 text-xs text-white transition-all ${inputErrorClass("age")}`} />
                  {shouldShowError("age") && <AlertCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none" />}
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500 ml-1">Education</Label>
                <div className="relative">
                    <select {...register("education")} className="w-full appearance-none bg-white/5 border border-white/10 rounded-xl h-11 text-xs px-4 outline-none focus:border-indigo-500/50 text-slate-200 transition-all cursor-pointer">
                        <option className="bg-[#020617]" value="Bachelor">Bachelor Degree</option>
                        <option className="bg-[#020617]" value="Master">Master Degree</option>
                        <option className="bg-[#020617]" value="PhD">PhD</option>
                        <option className="bg-[#020617]" value="None">Self Taught</option>
                    </select>
                    <ChevronDown size={14} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
                </div>
              </div>
            </div>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <div className="animate-in fade-in slide-in-from-right-4 duration-300 space-y-4">
              <div className="space-y-1.5">
                <Label className={`text-[10px] font-black uppercase tracking-[0.2em] ml-1 ${shouldShowError("password") ? 'text-red-400' : 'text-slate-500'}`}>Password (Min. 8 chars)</Label>
                <div className="relative">
                  <Input type="password" {...register("password")} placeholder="••••••••" className={`bg-white/5 border-white/10 rounded-xl h-11 text-xs text-white transition-all ${inputErrorClass("password")}`} />
                  {shouldShowError("password") && <AlertCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none" />}
                </div>
              </div>
              <div className="space-y-1.5">
                <Label className={`text-[10px] font-black uppercase tracking-[0.2em] ml-1 ${shouldShowError("confirmPassword") ? 'text-red-400' : 'text-slate-500'}`}>Confirm Password</Label>
                <div className="relative">
                  <Input type="password" {...register("confirmPassword")} placeholder="••••••••" className={`bg-white/5 border-white/10 rounded-xl h-11 text-xs text-white transition-all ${inputErrorClass("confirmPassword")}`} />
                  {shouldShowError("confirmPassword") && <AlertCircle size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500 pointer-events-none" />}
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            {step > 1 && (
                <button type="button" onClick={() => { clearErrors(); setStep(step - 1); }} className="flex-1 h-11 rounded-xl border border-white/5 text-[10px] font-bold uppercase tracking-widest text-slate-400 hover:text-white transition-all">Back</button>
            )}
            {step < 3 ? (
                <button type="button" onClick={nextStep} className="flex-[2] h-11 bg-white text-black hover:bg-slate-200 rounded-xl font-bold text-xs uppercase tracking-widest active:scale-95 transition-all shadow-xl shadow-white/5">Continue</button>
            ) : (
                <button type="submit" className="flex-[2] h-11 bg-indigo-600 text-white hover:bg-indigo-500 rounded-xl font-bold text-xs uppercase tracking-widest active:scale-95 transition-all shadow-lg shadow-indigo-500/20" disabled={isLoading}>
                    {isLoading ? "Processing..." : "Complete"}
                </button>
            )}
          </div>
        </form>

        <div className="mt-8">
          <p className="text-[11px] text-slate-500 font-medium">
            Member? <Link href="/login" className="text-indigo-400 uppercase tracking-wider font-bold hover:text-white transition-colors underline underline-offset-4 ml-1">Sign in</Link>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}