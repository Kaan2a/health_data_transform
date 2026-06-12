import { useCallback, useRef, useState, type DragEvent } from "react";
import ProgressBar from "./ui/ProgressBar";

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onUpload: (file: File) => Promise<void>;
  accept?: string;
  maxSizeMB?: number;
  isUploading?: boolean;
  uploadProgress?: number;
  uploadedFileName?: string | null;
}

const ALLOWED_EXTENSIONS = [".csv", ".tsv"];

export default function FileUpload({
  onFileSelect,
  onUpload,
  accept = ".csv,.tsv",
  maxSizeMB = 25,
  isUploading = false,
  uploadProgress = 0,
  uploadedFileName = null,
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      // Check extension
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        return `Geçersiz dosya türü. İzin verilen: ${ALLOWED_EXTENSIONS.join(", ")}`;
      }
      // Check size
      if (file.size > maxSizeMB * 1024 * 1024) {
        return `Dosya çok büyük. Maksimum: ${maxSizeMB} MB`;
      }
      if (file.size === 0) {
        return "Dosya boş.";
      }
      return null;
    },
    [maxSizeMB]
  );

  const handleFile = useCallback(
    (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError(validationError);
        setSelectedFile(null);
        return;
      }
      setError(null);
      setSelectedFile(file);
      onFileSelect(file);
    },
    [validateFile, onFileSelect]
  );

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleUploadClick = async () => {
    if (selectedFile) {
      await onUpload(selectedFile);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // Already uploaded state
  if (uploadedFileName) {
    return (
      <div className="rounded-xl border-2 border-emerald-200 bg-emerald-50/50 p-6" id="file-upload-done">
        <div className="flex items-center gap-3">
          <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
            <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-emerald-800">{uploadedFileName}</p>
            <p className="text-xs text-emerald-600 mt-0.5">Dosya başarıyla yüklendi</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3" id="file-upload">
      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative rounded-xl border-2 border-dashed p-8
          flex flex-col items-center justify-center gap-3
          cursor-pointer transition-all duration-200
          ${isDragging
            ? "border-indigo-400 bg-indigo-50/70 scale-[1.01]"
            : error
              ? "border-red-300 bg-red-50/30"
              : "border-slate-300 bg-slate-50/50 hover:border-indigo-300 hover:bg-indigo-50/30"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={handleInputChange}
          className="hidden"
          id="csv-file-input"
        />

        {/* Icon */}
        <div className={`
          w-12 h-12 rounded-xl flex items-center justify-center transition-colors duration-200
          ${isDragging ? "bg-indigo-100" : "bg-slate-100"}
        `}>
          <svg
            className={`w-6 h-6 ${isDragging ? "text-indigo-500" : "text-slate-400"}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        </div>

        {/* Text */}
        <div className="text-center">
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-indigo-600">Dosya seçin</span> veya sürükleyip bırakın
          </p>
          <p className="text-xs text-slate-400 mt-1">
            CSV veya TSV dosyaları • Maks. {maxSizeMB} MB
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-red-50 border border-red-200">
          <svg className="w-4 h-4 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
          <p className="text-xs text-red-600">{error}</p>
        </div>
      )}

      {/* Selected file info + upload button */}
      {selectedFile && !error && (
        <div className="flex items-center justify-between gap-3 px-4 py-3 rounded-xl bg-slate-50 border border-slate-200">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-700 truncate">{selectedFile.name}</p>
              <p className="text-xs text-slate-400">{formatFileSize(selectedFile.size)}</p>
            </div>
          </div>
          <button
            onClick={handleUploadClick}
            disabled={isUploading}
            className="
              px-4 py-2 text-sm font-medium rounded-lg
              bg-indigo-600 text-white
              hover:bg-indigo-700 active:bg-indigo-800
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-colors duration-150
              flex items-center gap-2 cursor-pointer
            "
            id="upload-button"
          >
            {isUploading ? (
              <>
                <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Yükleniyor...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
                </svg>
                Yükle
              </>
            )}
          </button>
        </div>
      )}

      {/* Upload progress */}
      {isUploading && (
        <ProgressBar value={uploadProgress} variant="primary" size="sm" />
      )}
    </div>
  );
}
