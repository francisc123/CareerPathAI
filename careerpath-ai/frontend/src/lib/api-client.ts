import axios from 'axios';

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor pentru a adăuga token-ul automat în viitor
api.interceptors.request.use((config) => {
  const authStorage = localStorage.getItem('auth-storage');
  if (authStorage) {
    const { state } = JSON.parse(authStorage);
    if (state.token) {
      config.headers.Authorization = `Bearer ${state.token}`;
    }
  }
  return config;
});

// Token expirat sau invalid → curăță sesiunea și trimite la login.
// Evită bucla pe ruta de login.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (typeof window !== 'undefined' && error?.response?.status === 401) {
      const onLogin = window.location.pathname.startsWith('/login');
      if (!onLogin) {
        try { localStorage.removeItem('auth-storage'); } catch {}
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Funcție pentru upload CV
export const uploadCV = async (file: File): Promise<{ job_id: string }> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/cv/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

// --- AI Agent endpoints ---
// Use API Gateway proxies for jobs and learning. These now go via /api/jobs
// and /api/learning so the frontend doesn't call agent ports directly.

export interface JobMatch {
  job_title: string;
  company: string;
  url: string;
  source: string;
  location: string;
  match_score: number;
  reason: string;
  generated_cover_letter: string;
}

export interface Resource {
  type: string;
  title: string;
  url: string;
}

export interface QuizQuestion {
  question: string;
  options: string[];
  correct_index: number;
}

export interface LearningModule {
  module_title: string;
  description: string;
  resources: Resource[];
  quiz: QuizQuestion[];
}

export interface WeeklyPlan {
  week: number;
  theme: string;
  modules: LearningModule[];
}

export interface LearningPath {
  user_id: string;
  target_role: string;
  title: string;
  estimated_weeks: number;
  weekly_plan: WeeklyPlan[];
}

export const getJobMatches = async (userId: string): Promise<{ matches: JobMatch[]; count: number }> => {
  const response = await api.get(`/jobs/${userId}`);
  return response.data;
};

export const getLearningPath = async (userId: string): Promise<LearningPath> => {
  const response = await api.get(`/learning/${userId}`);
  return response.data;
};

export const regenerateLearningPath = async (
  userId: string,
  targetRole: string,
  gaps?: string[],
): Promise<LearningPath> => {
  const response = await api.post('/learning/regenerate', {
    user_id: userId,
    target_role: targetRole,
    gaps: gaps ?? [],
  });
  return response.data;
};