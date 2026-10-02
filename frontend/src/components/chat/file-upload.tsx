"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { uploadFile } from "@/lib/api-client";
import { useChatStore } from "@/store/chat-store";
import { cn } from "@/lib/utils";
import { Upload, FileText, X, Loader2 } from "lucide-react";

interface FileUploadProps {
  onFileUploaded?: (filename: string, detectedType: string) => void;
}

export function FileUpload({ onFileUploaded }: FileUploadProps) {
  const { setUploadedFileName } = useChatStore();
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [detectedType, setDetectedType] = useState<string | null>(null);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setIsUploading(true);

      try {
        const result = await uploadFile(file);
        setUploadedFile(result.filename);
        setDetectedType(result.detected_type);
        setUploadedFileName(result.filename);

        onFileUploaded?.(result.filename, result.detected_type);
      } catch (err) {
        console.error("Upload failed:", err);
      } finally {
        setIsUploading(false);
      }
    },
    [setUploadedFileName, onFileUploaded]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "text/plain": [".txt"],
    },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const clearFile = () => {
    setUploadedFile(null);
    setDetectedType(null);
    setUploadedFileName(null);
  };

  if (uploadedFile) {
    return (
      <div className="flex items-center gap-2 p-2 bg-muted rounded-lg text-sm">
        <FileText className="h-4 w-4 text-muted-foreground" />
        <span className="flex-1 truncate">{uploadedFile}</span>
        <span className="text-xs text-muted-foreground">({detectedType})</span>
        <button
          onClick={clearFile}
          className="h-5 w-5 rounded-full hover:bg-destructive/20 flex items-center justify-center"
        >
          <X className="h-3 w-3" />
        </button>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={cn(
        "border-2 border-dashed rounded-lg p-3 text-center cursor-pointer transition-colors",
        isDragActive
          ? "border-primary bg-primary/5"
          : "border-muted-foreground/20 hover:border-muted-foreground/40",
        isUploading && "pointer-events-none opacity-50"
      )}
    >
      <input {...getInputProps()} />
      {isUploading ? (
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Uploading...
        </div>
      ) : isDragActive ? (
        <p className="text-sm text-primary font-medium">Drop file here...</p>
      ) : (
        <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
          <Upload className="h-4 w-4" />
          <span>Drop PDF or TXT here to upload</span>
        </div>
      )}
    </div>
  );
}