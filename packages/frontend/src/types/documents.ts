export type DocumentStatus = "uploaded" | "processing" | "ready";

export interface Document {
  readonly id: number;
  readonly file_name: string;
  readonly status: DocumentStatus;
  readonly meeting: number;
  readonly extracted_text: string | null;
}
