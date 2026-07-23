import axios from "axios";
import type { DocumentItem, Source } from "../types";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8080/api";

export const apiClient = axios.create({ baseURL });

export function setAuthToken(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common.Authorization = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common.Authorization;
  }
}

export interface AuthResponse {
  token: string;
  email: string;
}

export async function registerAccount(email: string, password: string): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/register", { email, password });
  return data;
}

export async function loginAccount(email: string, password: string): Promise<AuthResponse> {
  const { data } = await apiClient.post<AuthResponse>("/auth/login", { email, password });
  return data;
}

export async function fetchDocuments(): Promise<DocumentItem[]> {
  const { data } = await apiClient.get<DocumentItem[]>("/documents");
  return data;
}

export async function uploadDocument(file: File): Promise<DocumentItem> {
  const form = new FormData();
  form.append("file", file);
  const { data } = await apiClient.post<DocumentItem>("/documents", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function deleteDocument(id: string): Promise<void> {
  await apiClient.delete(`/documents/${id}`);
}

export interface QueryResponsePayload {
  answer: string;
  sources: Source[];
}

export async function sendQuery(question: string, topK = 5): Promise<QueryResponsePayload> {
  const { data } = await apiClient.post<QueryResponsePayload>("/chat/query", { question, topK });
  return data;
}

/** Pulls a readable message out of an Axios error, falling back to a generic one. */
export function readableError(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const response = (err as { response?: { data?: { error?: string } } }).response;
    if (response?.data?.error) return response.data.error;
  }
  return "Something went wrong. Please try again.";
}
