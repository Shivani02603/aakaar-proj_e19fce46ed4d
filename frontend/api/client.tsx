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
  name: string;
}

export interface SessionResponse {
  id: string;
  name: string;
  createdAt: string;
}

export interface MessageCreateRequest {
  sessionId: string;
  content: string;
}

export interface MessageResponse {
  id: string;
  sessionId: string;
  content: string;
  createdAt: string;
}

export interface FileUploadResponse {
  id: string;
  name: string;
  uploadedAt: string;
}

export interface QueryRequest {
  sessionId: string;
  query: string;
}

export interface QueryResponse {
  answer: string;
  citations: Array<{ source: string; excerpt: string }>;
}

// API client functions
export const createSession = (data: SessionCreateRequest) => api.post<SessionResponse>('/api/sessions', data);

export const listSessions = () => api.get<SessionResponse[]>('/api/sessions');

export const getSession = (sessionId: string) => api.get<SessionResponse>(`/api/sessions/${sessionId}`);

export const getSessionMessages = (sessionId: string) =>
  api.get<MessageResponse[]>(`/api/sessions/${sessionId}/messages`);

export const createMessage = (data: MessageCreateRequest) =>
  api.post<MessageResponse>(`/api/sessions/${data.sessionId}/messages`, { content: data.content });

export const uploadFile = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api.post<FileUploadResponse>('/api/upload', formData);
};

export const ingestDocuments = (fileId: string, sessionId: string) =>
  api.post('/api/ai/ingest', { fileId, sessionId });

export const aiQuery = (data: QueryRequest) => api.post<QueryResponse>('/api/ai/query', data);