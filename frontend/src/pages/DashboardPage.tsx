import { useCallback, useEffect, useState } from "react";
import { fetchDocuments } from "../api/client";
import { ChatPanel } from "../components/ChatPanel";
import { DocumentSidebar } from "../components/DocumentSidebar";
import { useAuth } from "../context/AuthContext";
import type { DocumentItem } from "../types";

export function DashboardPage() {
  const { email, logout } = useAuth();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoadingDocuments, setIsLoadingDocuments] = useState(true);

  const loadDocuments = useCallback(async () => {
    setIsLoadingDocuments(true);
    try {
      const docs = await fetchDocuments();
      setDocuments(docs);
    } finally {
      setIsLoadingDocuments(false);
    }
  }, []);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const hasReadyDocuments = documents.some((doc) => doc.status === "READY");

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <span className="brand-mark" aria-hidden="true">¶</span>
        <div className="dashboard-account">
          <span>{email}</span>
          <button type="button" className="btn-ghost" onClick={logout}>
            Sign out
          </button>
        </div>
      </header>
      <div className="dashboard-body">
        <DocumentSidebar
          documents={documents}
          isLoading={isLoadingDocuments}
          onDocumentsChanged={loadDocuments}
        />
        <ChatPanel hasReadyDocuments={hasReadyDocuments} />
      </div>
    </div>
  );
}
