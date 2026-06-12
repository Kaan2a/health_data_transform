import type { DataSourceResponse } from "../types/api";

interface DataSourceCardProps {
  source: DataSourceResponse;
  onUpload: () => void;
  onPreview: () => void;
  onDelete: () => void;
  onSelect: () => void;
}

const statusConfig: Record<string, { label: string; color: string; bgColor: string }> = {
  pending: { label: "Bekliyor", color: "text-slate-600", bgColor: "bg-slate-100" },
  uploaded: { label: "Yüklendi", color: "text-blue-600", bgColor: "bg-blue-100" },
  previewed: { label: "Önizlendi", color: "text-indigo-600", bgColor: "bg-indigo-100" },
  ready: { label: "Hazır", color: "text-emerald-600", bgColor: "bg-emerald-100" },
  error: { label: "Hata", color: "text-red-600", bgColor: "bg-red-100" },
};

export default function DataSourceCard({
  source,
  onUpload,
  onPreview,
  onDelete,
  onSelect,
}: DataSourceCardProps) {
  const status = statusConfig[source.status] ?? statusConfig.pending;

  const formatSize = (bytes: number | null): string => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (iso: string): string => {
    return new Date(iso).toLocaleDateString("tr-TR", {
      day: "numeric",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div
      className="group relative rounded-xl border border-slate-200 bg-white p-4 hover:shadow-md hover:border-slate-300 transition-all duration-200 cursor-pointer"
      onClick={onSelect}
      id={`source-card-${source.id}`}
    >
      <div className="flex items-start justify-between gap-3">
        {/* Icon + Info */}
        <div className="flex items-start gap-3 min-w-0">
          {/* Type icon */}
          <div className={`
            flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center
            ${source.type === "csv" ? "bg-emerald-100" : "bg-purple-100"}
          `}>
            {source.type === "csv" ? (
              <svg className="w-5 h-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
              </svg>
            )}
          </div>

          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-slate-800 truncate">{source.name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium ${status.bgColor} ${status.color}`}>
                {status.label}
              </span>
              <span className="text-xs text-slate-400 uppercase">{source.type}</span>
              {source.file_size_bytes && (
                <span className="text-xs text-slate-400">{formatSize(source.file_size_bytes)}</span>
              )}
            </div>
            {source.error_message && (
              <p className="text-xs text-red-500 mt-1 truncate" title={source.error_message}>
                {source.error_message}
              </p>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity duration-150">
          {source.type === "csv" && source.status === "pending" && (
            <ActionButton
              label="Dosya Yükle"
              icon={
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              }
              onClick={(e) => { e.stopPropagation(); onUpload(); }}
            />
          )}
          {source.type === "csv" && source.status === "uploaded" && (
            <ActionButton
              label="Önizle"
              icon={
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
              }
              onClick={(e) => { e.stopPropagation(); onPreview(); }}
            />
          )}
          <ActionButton
            label="Sil"
            icon={
              <path strokeLinecap="round" strokeLinejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" />
            }
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            danger
          />
        </div>
      </div>

      {/* Meta row */}
      <div className="flex items-center gap-3 mt-3 pt-3 border-t border-slate-100">
        {source.row_count != null && (
          <MetaItem label="Satır" value={source.row_count.toLocaleString("tr-TR")} />
        )}
        {source.columns && (
          <MetaItem label="Sütun" value={source.columns.length.toString()} />
        )}
        <MetaItem label="Oluşturulma" value={formatDate(source.created_at)} />
      </div>
    </div>
  );
}

function MetaItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-1">
      <span className="text-[10px] text-slate-400">{label}:</span>
      <span className="text-[10px] font-medium text-slate-600">{value}</span>
    </div>
  );
}

function ActionButton({
  label,
  icon,
  onClick,
  danger = false,
}: {
  label: string;
  icon: React.ReactNode;
  onClick: (e: React.MouseEvent) => void;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={label}
      className={`
        p-1.5 rounded-lg transition-colors duration-150 cursor-pointer
        ${danger
          ? "hover:bg-red-50 text-slate-400 hover:text-red-500"
          : "hover:bg-indigo-50 text-slate-400 hover:text-indigo-600"
        }
      `}
    >
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        {icon}
      </svg>
    </button>
  );
}
