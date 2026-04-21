import { create } from 'zustand';
import { persist } from 'zustand/middleware';

// Definim structura utilizatorului conform specificațiilor din User Service
interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  // Funcție pentru salvarea datelor după login
  setAuth: (user: User, token: string) => void;
  // Funcție pentru ștergerea datelor la logout
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      setAuth: (user, token) => set({ user, accessToken: token }),
      logout: () => set({ user: null, accessToken: null }),
    }),
    {
      name: 'auth-storage', // Numele cheii din browser (localStorage)
    }
  )
);