import { useRef, useState, type ChangeEvent } from "react";
import { deleteDocument, uploadDocument } from "../api/client";
import type { DocumentItem } from "../types";
import { StatusBadge } from "./StatusBadge";

interface Props {
  documents: DocumentItem[];
  isLoading: boolean;
  onDocumentsChanged: () => void;
}

const ACCEPTED = ".pdf,.docx,.txt";

export function DocumentSidebar({ documents, isLoading, onDocumentsChanged }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  async function handleFileChange(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    setUploadError(null);
    setIsUploading(true);
    try {
      await uploadDocument(file);
      onDocumentsChanged();
    } catch {
      setUploadError("Import failed. PDF, DOCX, and TXT only.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleDelete(id: string) {
    setDeletingId(id);
    try {
      await deleteDocument(id);
      onDocumentsChanged();
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2>Your documents</h2>
        <button
          type="button"
          className="btn-primary btn-sm"
          onClick={() => inputRef.current?.click()}
          disabled={isUploading}
        >
          {isUploading ? "Importing…" : "Import"}
        </button>
        <input ref={inputRef} type="file" accept={ACCEPTED} hidden onChange={handleFileChange} />
      </div>
      <p className="sidebar-hint">PDF, DOCX, or TXT</p>
      {uploadError && <p className="form-error">{uploadError}</p>}

      {isLoading ? (
        <p className="sidebar-empty">Loading…</p>
      ) : documents.length === 0 ? (
        <p className="sidebar-empty">No documents yet. Import one to get started.</p>
      ) : (
        <ul className="document-list">
          {documents.map((doc) => (
            <li key={doc.id} className="document-item">
              <div className="document-meta">
                <span className="document-filename">{doc.filename}</span>
                <span className="document-sub">
                  <StatusBadge status={doc.status} />
                  {doc.status === "FAILED" && doc.errorMessage && (
                    <span className="document-error" title={doc.errorMessage}>
                      {doc.errorMessage.length > 60
                        ? doc.errorMessage.substring(0, 60) + "…"
                        : doc.errorMessage}
                    </span>
                  )}
                  {doc.chunkCount != null && (
                    <span className="document-chunks">{doc.chunkCount} chunks</span>
                  )}
                </span>
              </div>
              <button
                type="button"
                className="btn-icon"
                aria-label={`Delete ${doc.filename}`}
                onClick={() => handleDelete(doc.id)}
                disabled={deletingId === doc.id}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </aside>
  );
}
