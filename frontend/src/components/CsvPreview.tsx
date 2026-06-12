interface ColumnInfo {
  name: string;
  inferred_type: string;
  sample_values: string[];
  null_count: number;
  total_count: number;
}

interface CsvPreviewProps {
  columns: ColumnInfo[];
  previewRows: Record<string, string>[];
  totalRows: number;
  encoding: string;
  delimiter: string;
}

const typeColorMap: Record<string, "blue" | "emerald" | "amber" | "purple"> = {
  string: "blue",
  number: "emerald",
  date: "amber",
  boolean: "purple",
};

const typeLabels: Record<string, string> = {
  string: "Metin",
  number: "Sayı",
  date: "Tarih",
  boolean: "Boolean",
};

export default function CsvPreview({
  columns,
  previewRows,
  totalRows,
  encoding,
  delimiter,
}: CsvPreviewProps) {
  return (
    <div className="space-y-4" id="csv-preview">
      {/* Stats bar */}
      <div className="flex flex-wrap items-center gap-3 px-4 py-2.5 rounded-lg bg-slate-50 border border-slate-200">
        <StatItem label="Toplam Satır" value={totalRows.toLocaleString("tr-TR")} />
        <Divider />
        <StatItem label="Sütun Sayısı" value={columns.length.toString()} />
        <Divider />
        <StatItem label="Kodlama" value={encoding.toUpperCase()} />
        <Divider />
        <StatItem
          label="Ayırıcı"
          value={delimiter === "," ? "Virgül" : delimiter === ";" ? "Noktalı virgül" : delimiter === "\t" ? "Tab" : delimiter}
        />
      </div>

      {/* Column metadata cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
        {columns.map((col) => (
          <div
            key={col.name}
            className="px-3 py-2.5 rounded-lg border border-slate-200 bg-white hover:shadow-sm transition-shadow duration-150"
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className="text-xs font-semibold text-slate-700 truncate" title={col.name}>
                {col.name}
              </span>
            </div>
            <div className="flex items-center gap-1.5">
              <TypeBadge type={col.inferred_type} />
              {col.null_count > 0 && (
                <span className="text-[10px] text-slate-400">
                  {col.null_count} boş
                </span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Preview table */}
      <div
        className="overflow-auto rounded-lg border border-slate-200 shadow-sm"
        style={{ maxHeight: "400px" }}
      >
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50 sticky top-0 z-10">
            <tr>
              <th className="px-3 py-2.5 text-left text-[10px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-200 bg-slate-50 w-12">
                #
              </th>
              {columns.map((col) => (
                <th
                  key={col.name}
                  className="px-3 py-2.5 text-left text-xs font-semibold text-slate-600 border-b border-slate-200 bg-slate-50 whitespace-nowrap"
                >
                  <div className="flex items-center gap-1.5">
                    {col.name}
                    <TypeBadge type={col.inferred_type} small />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-100">
            {previewRows.map((row, rowIdx) => (
              <tr key={rowIdx} className="hover:bg-indigo-50/30 transition-colors duration-75">
                <td className="px-3 py-2 text-xs text-slate-400 font-mono">
                  {rowIdx + 1}
                </td>
                {columns.map((col) => (
                  <td key={col.name} className="px-3 py-2 text-sm text-slate-700 whitespace-nowrap max-w-[200px] truncate">
                    {row[col.name] || <span className="text-slate-300 italic">null</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Row count footer */}
      {previewRows.length < totalRows && (
        <p className="text-xs text-slate-400 text-center">
          İlk {previewRows.length} satır gösteriliyor — toplam {totalRows.toLocaleString("tr-TR")} satır
        </p>
      )}
    </div>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs text-slate-400">{label}:</span>
      <span className="text-xs font-semibold text-slate-700">{value}</span>
    </div>
  );
}

function Divider() {
  return <div className="w-px h-3.5 bg-slate-200" />;
}

function TypeBadge({ type, small = false }: { type: string; small?: boolean }) {
  const color = typeColorMap[type] ?? "blue";
  const label = typeLabels[type] ?? type;

  const colorClasses = {
    blue: "bg-blue-100 text-blue-700",
    emerald: "bg-emerald-100 text-emerald-700",
    amber: "bg-amber-100 text-amber-700",
    purple: "bg-purple-100 text-purple-700",
  };

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full
        ${colorClasses[color]}
        ${small ? "text-[9px] px-1.5 py-0" : "text-[10px] px-2 py-0.5"}
      `}
    >
      {label}
    </span>
  );
}
