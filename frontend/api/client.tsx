import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || '',
});

// Request interceptor
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// TypeScript interfaces for request/response types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
}

export interface SessionCreateRequest {
  title: string;
}

export interface SessionResponse {
  id: string;
  title: string;
  createdAt: string;
}

export interface MessageCreateRequest {
  sessionId: string;
  content: string;
}

export interface MessageResponse {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  createdAt: string;
}

export interface FileUploadResponse {
  id: string;
  source: string;
  createdAt: string;
}

export interface QueryRequest {
  query: string;
  sessionId: string;
}

export interface QueryResponse {
  answer: string;
  citations: Array<{ source: string; snippet: string }>;
}

// API client functions
export const createSession = (data: SessionCreateRequest) => api.post<SessionResponse>('/api/sessions', data);

export const listSessions = () => api.get<SessionResponse[]>('/api/sessions');

export const getSession = (sessionId: string) => api.get<SessionResponse>(`/api/sessions/${sessionId}`);

export const getSessionMessages = (sessionId: string) =>
  api.get<MessageResponse[]>(`/api/sessions/${sessionId}/messages`);

export const uploadFile = (formData: FormData) => api.post<FileUploadResponse>('/api/upload', formData);

export const ingestDocuments = (data: { fileId: string; sessionId: string }) =>
  api.post('/api/ai/ingest', data);

export const aiQuery = (data: QueryRequest) => api.post<QueryResponse>('/api/ai/query', data);