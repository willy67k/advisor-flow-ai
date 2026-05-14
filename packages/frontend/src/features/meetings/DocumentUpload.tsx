import { useCallback, useEffect, useState } from "react";
import { useDropzone } from "react-dropzone";

import { fetchDocumentsByMeeting, uploadDocument } from "../../services/documentsApi";
import type { Document } from "../../types/documents";

interface Props {
  readonly meetingId: number;
}

const STATUS_LABEL: Record = {
  uploaded: "Queued",
  processing: "Processing…",
  ready: "Ready",
};

const STATUS_COLOR: Record = {
  uploaded: "text-slate-400",
  processing: "text-amber-400",
  ready: "text-emerald-400",
};

export function DocumentUpload({ meetingId }: Props) {
  const [docs, setDocs] = useState<Document[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadDocs = useCallback(async () => {
    try {
      const result = await fetchDocumentsByMeeting(meetingId);
      setDocs(result);
    } catch {
      // silently fail; initial docs load non-critical
    }
  }, [meetingId]);

  useEffect(() => {
    void loadDocs();
  }, [loadDocs]);

  // Poll processing docs every 4s
  useEffect(() => {
    const hasProcessing = docs.some((d) => d.status === "uploaded" || d.status === "processing");
    if (!hasProcessing) return;
    const id = setInterval(() => void loadDocs(), 4000);
    return () => clearInterval(id);
  }, [docs, loadDocs]);

  const onDrop = useCallback(
    async (accepted: File[]) => {
      if (accepted.length === 0) return;
      setError(null);
      setUploading(true);
      try {
        for (const file of accepted) {
          const doc = await uploadDocument(meetingId, file);
          setDocs((prev) => [doc, ...prev]);
        }
      } catch {
        setError("Upload failed. Accepted formats: PDF, DOC, DOCX.");
      } finally {
        setUploading(false);
      }
    },
    [meetingId],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/msword": [".doc"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
    },
    multiple: true,
    disabled: uploading,
  });

  return (
    <div className="space-y-3">
      <div
        {...getRootProps()}
        className={`cursor-pointer rounded-lg border-2 border-dashed px-4 py-6 text-center transition ${isDragActive ? "border-emerald-500 bg-emerald-500/5" : "border-slate-700 hover:border-slate-500"} ${
          uploading ? "pointer-events-none opacity-50" : ""
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-slate-400">{isDragActive ? "Drop files here…" : uploading ? "Uploading…" : "Drag & drop PDF / Word files, or click to browse"}</p>
      </div>

      {error ? <p className="text-xs text-rose-400">{error}</p> : null}

      {docs.length > 0 ? (
        <ul className="divide-y divide-slate-800 overflow-hidden rounded-lg border border-slate-800">
          {docs.map((doc) => (
            <li key={doc.id} className="flex items-center justify-between gap-3 bg-slate-900/60 px-4 py-3">
              <span className="min-w-0 truncate text-sm text-slate-200">{doc.file_name}</span>
              <span className={`shrink-0 text-xs font-medium ${STATUS_COLOR[doc.status] ?? "text-slate-400"}`}>{STATUS_LABEL[doc.status] ?? doc.status}</span>
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
