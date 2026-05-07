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
// NOTE for Francis: These call agents directly because API Gateway doesn't yet
// have routes for /api/jobs and /api/learning. Add proxy routes to api-gateway
// pointing to cp-job-match-agent:8007 and cp-learning-path-agent:8008.

const JOB_AGENT_URL = process.env.NEXT_PUBLIC_JOB_AGENT_URL || 'http://localhost:8007';
const LEARNING_AGENT_URL = process.env.NEXT_PUBLIC_LEARNING_AGENT_URL || 'http://localhost:8008';

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

export interface LearningModule {
  module_title: string;
  description: string;
  resources: { type: string; title: string; url: string }[];
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
  plan_data: WeeklyPlan[];
}

export const getJobMatches = async (userId: string): Promise<{ matches: JobMatch[]; count: number }> => {
  const response = await axios.get(`${JOB_AGENT_URL}/jobs/${userId}`);
  return response.data;
};

export const getLearningPath = async (userId: string): Promise<LearningPath> => {
  const response = await axios.get(`${LEARNING_AGENT_URL}/learning/${userId}`);
  return response.data;
};