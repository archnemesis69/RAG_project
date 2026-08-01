export type DocumentStatus = "PROCESSING" | "READY" | "FAILED";

export interface DocumentItem {
  id: string;
  filename: string;
  status: DocumentStatus;
  chunkCount: number | null;
  errorMessage: string | null;
  uploadedAt: string;
}

export interface Source {
  source: string | null;
  page: number | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
}
