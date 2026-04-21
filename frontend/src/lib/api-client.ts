import axios from 'axios';
import { useAuthStore } from '../store/zustand/auth.store';

export const apiClient = axios.create({
  baseURL: '/api', // Se bazează pe rewrite-ul din next.config.mjs
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor pentru cereri: adaugă automat Header-ul de Authorization
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor pentru răspunsuri: gestionează erorile de tip 401 (Unauthorized)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Dacă primim 401, înseamnă că token-ul nu mai e valid
    if (error.response && error.response.status === 401) {
      useAuthStore.getState().logout();
      if (typeof window !== 'undefined') {
        window.location.href = '/login'; // Redirecționare forțată la login
      }
    }
    return Promise.reject(error);
  }
);