import * as z from "zod";

export const loginSchema = z.object({
  email: z.string().min(1, "Emailul este obligatoriu").email("Email invalid"),
  password: z.string().min(8, "Minim 8 caractere"),
});

export const registerSchema = z.object({
  name: z.string().min(2, "Minim 2 caractere"),
  email: z.string().min(1, "Emailul este obligatoriu").email("Email invalid"),
  password: z.string().min(8, "Minim 8 caractere"),
  confirmPassword: z.string().min(1, "Confirmarea este obligatorie"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Parolele nu se potrivesc",
  path: ["confirmPassword"],
});